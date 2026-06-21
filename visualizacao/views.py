from datetime import date
from decimal import Decimal

from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from contas.models import Conta
from lancamentos.models import Lancamento
from meses.models import MesAberto, SaldoMensalConta
from meses.services import (
    ajustar_saldo_inicial,
    criar_mes,
    mes_anterior_posterior,
    pendentes_mes_anterior,
    saldo_do_mes,
    saldo_investimento,
    transferir_pendente_para_mes,
)


def _filtros_mes(request):
    hoje = date.today()
    try:
        ano = int(request.POST.get("ano") or request.GET.get("ano", hoje.year))
        mes = int(request.POST.get("mes") or request.GET.get("mes", hoje.month))
    except (TypeError, ValueError):
        return hoje.year, hoje.month

    if not 1 <= mes <= 12:
        return hoje.year, hoje.month

    return ano, mes


def _parse_status(request):
    status = request.GET.getlist("status")
    return [item.upper() for item in status] if status else None


def _carregar_mes(ano, mes):
    mes_aberto, _, pendentes, aviso_limite = criar_mes(ano, mes)
    return mes_aberto, pendentes, aviso_limite


@require_http_methods(["GET"])
def visao_consolidada(request):
    ano, mes = _filtros_mes(request)
    if not MesAberto.objects.filter(ano=ano, mes=mes).exists():
        return render(request, "visualizacao/mes_nao_criado.html", {"ano": ano, "mes": mes})

    conta_id = request.GET.get("conta")
    status = _parse_status(request)

    contas_base = Conta.objects.filter(tipo__in=[Conta.Tipo.BANCO, Conta.Tipo.CARTAO]).order_by("nome")
    lancamentos = Lancamento.objects.filter(
        competencia_ano=ano,
        competencia_mes=mes,
        conta__in=contas_base,
    ).select_related("conta").order_by("data_vencimento", "id")

    if conta_id:
        lancamentos = lancamentos.filter(conta_id=conta_id)

    lancamentos_lista = list(lancamentos)
    if status:
        status_set = set(status)
        lancamentos_lista = [l for l in lancamentos_lista if l.status in status_set]

    entradas = Decimal("0.00")
    saidas = Decimal("0.00")
    for item in lancamentos_lista:
        if item.direcao == "ENTRADA":
            entradas += item.valor_absoluto
        else:
            saidas += item.valor_absoluto

    saldo_total = Decimal("0.00")
    contas_ajuste = []
    for conta in contas_base:
        saldo_total += saldo_do_mes(conta, ano, mes, status_incluidos=status)
        saldo_inicial = (
            SaldoMensalConta.objects.filter(conta=conta, ano=ano, mes=mes)
            .values_list("saldo_inicial", flat=True)
            .first()
        )
        contas_ajuste.append(
            {
                "conta": conta,
                "saldo_inicial": saldo_inicial if saldo_inicial is not None else (conta.saldo_atual or Decimal("0.00")),
            }
        )

    alertas_limite = []
    for conta in contas_base.filter(tipo=Conta.Tipo.BANCO):
        saldo_conta = saldo_do_mes(conta, ano, mes, status_incluidos=status)
        if conta.limite_negativo_ultrapassado(saldo_conta):
            alertas_limite.append(f"{conta.nome}: limite negativo ultrapassado.")
        elif conta.limite_negativo_proximo(saldo_conta):
            alertas_limite.append(f"{conta.nome}: saldo proximo do limite negativo.")

    (ano_ant, mes_ant), (ano_prox, mes_prox) = mes_anterior_posterior(ano, mes)
    aviso_limite = request.session.pop("aviso_limite_meses", None)

    return render(
        request,
        "visualizacao/consolidada.html",
        {
            "ano": ano,
            "mes": mes,
            "ano_ant": ano_ant,
            "mes_ant": mes_ant,
            "ano_prox": ano_prox,
            "mes_prox": mes_prox,
            "contas": Conta.objects.all().order_by("nome"),
            "conta_selecionada": int(conta_id) if conta_id else None,
            "lancamentos": lancamentos_lista,
            "status_ativos": status or [],
            "total_entradas": entradas,
            "total_saidas": saidas,
            "saldo_total": saldo_total,
            "contas_ajuste": contas_ajuste,
            "pendentes_mes_anterior": pendentes_mes_anterior(ano, mes),
            "alertas_limite": alertas_limite,
            "aviso_limite_meses": aviso_limite,
        },
    )


@require_http_methods(["GET"])
def visao_patrimonio(request):
    contas = Conta.objects.filter(tipo=Conta.Tipo.INVESTIMENTO).order_by("nome")
    dados = []
    for conta in contas:
        lancamentos = Lancamento.objects.filter(
            conta=conta,
            tipo__in=[Lancamento.Tipo.APORTE, Lancamento.Tipo.RESGATE],
        ).order_by("data_vencimento")
        dados.append(
            {
                "conta": conta,
                "saldo": saldo_investimento(conta),
                "movimentos": lancamentos,
            }
        )
    return render(request, "visualizacao/patrimonio.html", {"dados": dados})


@require_http_methods(["GET"])
def comparativo_meses(request):
    hoje = date.today()
    ano_a = int(request.GET.get("ano_a", hoje.year))
    mes_a = int(request.GET.get("mes_a", hoje.month))
    ano_b = int(request.GET.get("ano_b", hoje.year if hoje.month > 1 else hoje.year - 1))
    mes_b = int(request.GET.get("mes_b", hoje.month - 1 or 12))

    contas = Conta.objects.filter(tipo__in=[Conta.Tipo.BANCO, Conta.Tipo.CARTAO]).order_by("nome")
    linhas = []
    for conta in contas:
        saldo_a = saldo_do_mes(conta, ano_a, mes_a)
        saldo_b = saldo_do_mes(conta, ano_b, mes_b)
        linhas.append(
            {
                "conta": conta,
                "saldo_a": saldo_a,
                "saldo_b": saldo_b,
                "variacao": saldo_a - saldo_b,
            }
        )

    return render(
        request,
        "visualizacao/comparativo.html",
        {
            "ano_a": ano_a,
            "mes_a": mes_a,
            "ano_b": ano_b,
            "mes_b": mes_b,
            "linhas": linhas,
        },
    )


@require_http_methods(["POST"])
def transferir_pendente(request, pk):
    ano, mes = _filtros_mes(request)
    try:
        lancamento = Lancamento.objects.get(pk=pk)
    except Lancamento.DoesNotExist:
        return HttpResponseBadRequest("Lancamento nao encontrado.")
    transferir_pendente_para_mes(lancamento, ano, mes)
    return render(request, "visualizacao/_flash.html", {"mensagem": "Lancamento transferido para o mes atual."})


@require_http_methods(["POST"])
def manter_pendente(request, pk):
    if not Lancamento.objects.filter(pk=pk).exists():
        return HttpResponseBadRequest("Lancamento nao encontrado.")
    return render(request, "visualizacao/_flash.html", {"mensagem": "Lancamento mantido no mes anterior."})


@require_http_methods(["POST"])
def ajustar_saldo(request, conta_id):
    ano, mes = _filtros_mes(request)
    novo_saldo = request.POST.get("novo_saldo")
    if novo_saldo is None:
        return HttpResponseBadRequest("Campo novo_saldo e obrigatorio.")

    try:
        conta = Conta.objects.get(pk=conta_id)
    except Conta.DoesNotExist:
        return HttpResponseBadRequest("Conta nao encontrada.")

    try:
        saldo_decimal = Decimal(novo_saldo)
    except Exception:
        return HttpResponseBadRequest("Campo novo_saldo deve ser um decimal valido.")

    _, conciliacao = ajustar_saldo_inicial(conta, ano, mes, saldo_decimal)
    mensagem = "Saldo inicial atualizado."
    if conciliacao:
        mensagem += " Lancamento de Conciliacao gerado automaticamente."
    return render(request, "visualizacao/_flash.html", {"mensagem": mensagem})


@require_http_methods(["POST"])
def criar_mes_view(request):
    ano, mes = _filtros_mes(request)
    _, _, aviso_limite = _carregar_mes(ano, mes)
    if aviso_limite:
        request.session["aviso_limite_meses"] = "Limite recomendado de 12 meses futuros foi ultrapassado."
    return redirect(f"/?ano={ano}&mes={mes}")
