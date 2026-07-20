from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from contas.models import Conta
from lancamentos.models import Lancamento
from meses.models import MesAberto
from meses.services import (
    saldo_investimento,
    saldo_projetado_em_data,
    saldo_real_em_data,
    saldos_do_mes,
    total_gastos_cartao_por_mes,
)


@dataclass(frozen=True)
class ResumoMes:
    lancamentos: list
    total_entradas: Decimal
    total_saidas: Decimal
    saldo_total: Decimal
    contas_ajuste: list
    alertas_limite: list
    conta_selecionada: Conta | None


def resumo_consolidado(ano, mes, conta_id=None, status=None):
    """Computa o resumo consolidado do mes para contas Banco e Cartao.

    Retorna lancamentos filtrados, totais, saldos por conta e alertas de
    limite com numero constante de consultas (4): contas, lancamentos
    exibidos e as duas de meses.services.saldos_do_mes — a implementacao
    unica da regra de saldo mensal, da qual saem os saldos iniciais
    (contas_ajuste) e finais (saldo_total, alertas).
    """
    contas_base = list(
        Conta.objects.filter(tipo__in=[Conta.Tipo.BANCO, Conta.Tipo.CARTAO]).order_by("nome")
    )

    lancamentos_mes = (
        Lancamento.objects.filter(
            competencia_ano=ano,
            competencia_mes=mes,
            conta__in=[conta.pk for conta in contas_base],
        )
        .select_related("conta", "lancamento_vinculado__conta")
        .order_by("data_vencimento", "id")
    )
    if status:
        lancamentos_mes = lancamentos_mes.com_status_in(status)
    lancamentos_mes = list(lancamentos_mes)

    conta_selecionada = None
    if conta_id:
        conta_selecionada = next((c for c in contas_base if c.pk == conta_id), None)
        lancamentos_exibidos = [item for item in lancamentos_mes if item.conta_id == conta_id]
    else:
        lancamentos_exibidos = lancamentos_mes

    total_entradas = Decimal("0.00")
    total_saidas = Decimal("0.00")
    for item in lancamentos_exibidos:
        if item.direcao == "ENTRADA":
            total_entradas += item.valor_absoluto
        else:
            total_saidas += item.valor_absoluto

    saldos = saldos_do_mes(contas_base, ano, mes, status_incluidos=status)
    contas_ajuste = [
        {"conta": conta, "saldo_inicial": saldos[conta.pk].inicial} for conta in contas_base
    ]
    saldo_por_conta = {conta.pk: saldos[conta.pk].final for conta in contas_base}

    if conta_selecionada:
        saldo_total = saldo_por_conta[conta_selecionada.pk]
    else:
        saldo_total = sum(saldo_por_conta.values(), Decimal("0.00"))

    alertas_limite = []
    for conta in contas_base:
        if conta.tipo != Conta.Tipo.BANCO:
            continue
        saldo_conta = saldo_por_conta[conta.pk]
        if conta.limite_negativo_ultrapassado(saldo_conta):
            alertas_limite.append(f"{conta.nome}: limite negativo ultrapassado.")
        elif conta.limite_negativo_proximo(saldo_conta):
            alertas_limite.append(f"{conta.nome}: saldo proximo do limite negativo.")

    return ResumoMes(
        lancamentos=lancamentos_exibidos,
        total_entradas=total_entradas,
        total_saidas=total_saidas,
        saldo_total=saldo_total,
        contas_ajuste=contas_ajuste,
        alertas_limite=alertas_limite,
        conta_selecionada=conta_selecionada,
    )


@dataclass(frozen=True)
class SaldoBancoItem:
    conta: Conta
    saldo_real: Decimal
    saldo_projetado: Decimal


@dataclass(frozen=True)
class FaturaCartaoItem:
    conta: Conta
    faturas: list  # lista de dicts {ano, mes, total}


@dataclass(frozen=True)
class SaldoInvestimentoItem:
    conta: Conta
    saldo: Decimal


@dataclass(frozen=True)
class ResumoPlanejamento:
    data_ref: date
    mes_ref_ano: int
    mes_ref_mes: int
    data_fora_mes_aberto: bool
    bancos: list  # list[SaldoBancoItem]
    total_real_banco: Decimal
    total_projetado_banco: Decimal
    cartoes: list  # list[FaturaCartaoItem]
    meses_cartao: list  # list of (ano, mes) tuples — colunas da tabela
    investimentos: list  # list[SaldoInvestimentoItem]
    total_investimentos: Decimal
    sem_meses_abertos: bool


def planejamento_financeiro(data_ref: date) -> ResumoPlanejamento:
    """Computa o resumo de planejamento financeiro para a data de referencia.

    Retorna saldos reais e projetados para contas Banco, totais de fatura
    por mes para contas Cartao (ate 4 meses), e saldos reais de
    contas Investimento.
    """
    ultimo_mes = MesAberto.objects.order_by("-ano", "-mes").first()
    sem_meses_abertos = ultimo_mes is None

    if sem_meses_abertos:
        return ResumoPlanejamento(
            data_ref=data_ref,
            mes_ref_ano=data_ref.year,
            mes_ref_mes=data_ref.month,
            data_fora_mes_aberto=False,
            bancos=[],
            total_real_banco=Decimal("0.00"),
            total_projetado_banco=Decimal("0.00"),
            cartoes=[],
            meses_cartao=[],
            investimentos=[],
            total_investimentos=Decimal("0.00"),
            sem_meses_abertos=True,
        )

    data_fora_mes_aberto = not MesAberto.objects.filter(
        ano=data_ref.year, mes=data_ref.month
    ).exists()

    # Determina mes de referencia efetivo (pode ser diferente da data se mes nao aberto)
    if data_fora_mes_aberto:
        mes_ref_ano = ultimo_mes.ano
        mes_ref_mes = ultimo_mes.mes
    else:
        mes_ref_ano = data_ref.year
        mes_ref_mes = data_ref.month

    # Contas Banco
    contas_banco = list(Conta.objects.filter(tipo=Conta.Tipo.BANCO).order_by("nome"))
    bancos = []
    total_real = Decimal("0.00")
    total_projetado = Decimal("0.00")
    for conta in contas_banco:
        real = saldo_real_em_data(conta, data_ref)
        projetado = saldo_projetado_em_data(conta, data_ref)
        bancos.append(SaldoBancoItem(conta=conta, saldo_real=real, saldo_projetado=projetado))
        total_real += real
        total_projetado += projetado

    # Contas Cartao
    contas_cartao = list(Conta.objects.filter(tipo=Conta.Tipo.CARTAO).order_by("nome"))
    gastos_por_mes = total_gastos_cartao_por_mes(contas_cartao)
    meses_cartao = sorted(gastos_por_mes.keys())
    cartoes = []
    for conta in contas_cartao:
        faturas = [
            {"ano": ano, "mes": mes, "total": gastos_por_mes[(ano, mes)].get(conta.pk, Decimal("0.00"))}
            for ano, mes in meses_cartao
        ]
        cartoes.append(FaturaCartaoItem(conta=conta, faturas=faturas))

    # Contas Investimento
    contas_invest = list(Conta.objects.filter(tipo=Conta.Tipo.INVESTIMENTO).order_by("nome"))
    investimentos = []
    total_invest = Decimal("0.00")
    for conta in contas_invest:
        saldo = saldo_investimento(conta)
        investimentos.append(SaldoInvestimentoItem(conta=conta, saldo=saldo))
        total_invest += saldo

    return ResumoPlanejamento(
        data_ref=data_ref,
        mes_ref_ano=mes_ref_ano,
        mes_ref_mes=mes_ref_mes,
        data_fora_mes_aberto=data_fora_mes_aberto,
        bancos=bancos,
        total_real_banco=total_real,
        total_projetado_banco=total_projetado,
        cartoes=cartoes,
        meses_cartao=meses_cartao,
        investimentos=investimentos,
        total_investimentos=total_invest,
        sem_meses_abertos=False,
    )
