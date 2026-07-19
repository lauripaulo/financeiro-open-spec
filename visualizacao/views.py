from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from contas.models import Conta
from lancamentos.models import Lancamento
from meses.models import MesAberto
from meses.services import (
    ajustar_saldo_inicial,
    criar_mes,
    mes_anterior_posterior,
    mes_permitido_para_abertura,
    pendentes_mes_anterior,
    saldo_do_mes,
    saldo_investimento,
    transferir_pendente_para_mes,
)
from visualizacao.services import resumo_consolidado


def _erro(request, mensagem):
    if request.headers.get("HX-Request"):
        messages.error(request, mensagem)
        return HttpResponse(status=204, headers={"HX-Refresh": "true"})
    return HttpResponseBadRequest(mensagem)


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
        ano_permitido, mes_permitido = mes_permitido_para_abertura()
        return render(
            request,
            "visualizacao/mes_nao_criado.html",
            {
                "ano": ano,
                "mes": mes,
                "mes_permitido_ano": ano_permitido,
                "mes_permitido_mes": mes_permitido,
            },
        )

    conta_param = request.GET.get("conta")
    conta_id = int(conta_param) if conta_param else None
    status = _parse_status(request)

    resumo = resumo_consolidado(ano, mes, conta_id=conta_id, status=status)

    paginador = Paginator(resumo.lancamentos, 50)
    pagina = paginador.get_page(request.GET.get("pagina"))

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
            "conta_selecionada": conta_id,
            "conta_selecionada_obj": resumo.conta_selecionada,
            "lancamentos": pagina,
            "pagina": pagina,
            "status_ativos": status or [],
            "total_entradas": resumo.total_entradas,
            "total_saidas": resumo.total_saidas,
            "saldo_total": resumo.saldo_total,
            "contas_ajuste": resumo.contas_ajuste,
            "pendentes_mes_anterior": pendentes_mes_anterior(ano, mes),
            "alertas_limite": resumo.alertas_limite,
            "aviso_limite_meses": aviso_limite,
        },
    )


@require_http_methods(["GET"])
def visao_patrimonio(request):
    contas = Conta.objects.filter(tipo=Conta.Tipo.INVESTIMENTO).order_by("nome")
    dados = []
    total_patrimonio = Decimal("0.00")
    for conta in contas:
        saldo = saldo_investimento(conta)
        lancamentos = Lancamento.objects.filter(
            conta=conta,
            tipo__in=[Lancamento.Tipo.APORTE, Lancamento.Tipo.RESGATE],
        ).select_related("lancamento_vinculado__conta").order_by("data_vencimento")
        dados.append(
            {
                "conta": conta,
                "saldo": saldo,
                "movimentos": lancamentos,
            }
        )
        total_patrimonio += saldo
    return render(
        request,
        "visualizacao/patrimonio.html",
        {
            "dados": dados,
            "total_patrimonio": total_patrimonio,
        },
    )


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
        return _erro(request, "Lancamento nao encontrado.")
    try:
        transferir_pendente_para_mes(lancamento, ano, mes)
    except ValidationError as exc:
        return _erro(request, " ".join(exc.messages))
    messages.success(request, "Lancamento transferido para o mes atual.")
    return HttpResponse(status=204, headers={"HX-Refresh": "true"})


@require_http_methods(["POST"])
def manter_pendente(request, pk):
    if not Lancamento.objects.filter(pk=pk).exists():
        return _erro(request, "Lancamento nao encontrado.")
    messages.success(request, "Lancamento mantido no mes anterior.")
    return HttpResponse(status=204, headers={"HX-Refresh": "true"})


@require_http_methods(["POST"])
def ajustar_saldo(request, conta_id):
    ano, mes = _filtros_mes(request)
    novo_saldo = request.POST.get("novo_saldo")
    if not novo_saldo:
        return _erro(request, "Campo novo_saldo e obrigatorio.")

    try:
        conta = Conta.objects.get(pk=conta_id)
    except Conta.DoesNotExist:
        return _erro(request, "Conta nao encontrada.")

    try:
        saldo_decimal = Decimal(novo_saldo)
    except Exception:
        return _erro(request, "Campo novo_saldo deve ser um decimal valido.")

    _, conciliacao = ajustar_saldo_inicial(conta, ano, mes, saldo_decimal)
    mensagem = "Saldo inicial atualizado."
    if conciliacao:
        mensagem += " Lancamento de Conciliacao gerado automaticamente."
    messages.success(request, mensagem)
    return HttpResponse(status=204, headers={"HX-Refresh": "true"})


@require_http_methods(["POST"])
def criar_mes_view(request):
    ano, mes = _filtros_mes(request)
    try:
        _, pendentes, aviso_limite = _carregar_mes(ano, mes)
    except ValidationError as exc:
        mensagem = " ".join(exc.messages)
        ano_permitido, mes_permitido = mes_permitido_para_abertura()
        return render(
            request,
            "visualizacao/mes_nao_criado.html",
            {
                "ano": ano,
                "mes": mes,
                "erro_validacao": mensagem,
                "mes_permitido_ano": ano_permitido,
                "mes_permitido_mes": mes_permitido,
            },
        )
    if aviso_limite:
        request.session["aviso_limite_meses"] = "Limite recomendado de 12 meses futuros foi ultrapassado."
    if pendentes.exists():
        return redirect(f"{reverse('visualizacao:resolver_pendentes_abertura')}?ano={ano}&mes={mes}")
    return redirect(f"/?ano={ano}&mes={mes}")


@require_http_methods(["GET"])
def resolver_pendentes_abertura(request):
    ano, mes = _filtros_mes(request)
    pendentes = pendentes_mes_anterior(ano, mes)
    if not pendentes.exists():
        return redirect(f"/?ano={ano}&mes={mes}")
    return render(
        request,
        "visualizacao/resolver_pendentes.html",
        {"ano": ano, "mes": mes, "pendentes": pendentes},
    )
