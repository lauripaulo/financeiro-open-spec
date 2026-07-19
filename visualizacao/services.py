from dataclasses import dataclass
from decimal import Decimal

from contas.models import Conta
from lancamentos.models import Lancamento
from meses.models import SaldoMensalConta


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
    limite em passada unica: uma consulta de lancamentos do mes e uma de
    SaldoMensalConta. A regra de saldo aplicada por conta e a mesma de
    meses.services.saldo_do_mes (saldo inicial com fallback em
    conta.saldo_atual + entradas - saidas).
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
        conta_id = int(conta_id)
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

    saldos_iniciais_registrados = dict(
        SaldoMensalConta.objects.filter(conta__in=contas_base, ano=ano, mes=mes).values_list(
            "conta_id", "saldo_inicial"
        )
    )

    movimento_por_conta = {conta.pk: Decimal("0.00") for conta in contas_base}
    for item in lancamentos_mes:
        if item.direcao == "ENTRADA":
            movimento_por_conta[item.conta_id] += item.valor_absoluto
        else:
            movimento_por_conta[item.conta_id] -= item.valor_absoluto

    contas_ajuste = []
    saldo_por_conta = {}
    for conta in contas_base:
        saldo_inicial = saldos_iniciais_registrados.get(conta.pk)
        if saldo_inicial is None:
            saldo_inicial = conta.saldo_atual or Decimal("0.00")
        contas_ajuste.append({"conta": conta, "saldo_inicial": saldo_inicial})
        saldo_por_conta[conta.pk] = saldo_inicial + movimento_por_conta[conta.pk]

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
