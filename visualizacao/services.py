from dataclasses import dataclass
from decimal import Decimal

from contas.models import Conta
from lancamentos.models import Lancamento
from meses.services import saldos_do_mes


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
