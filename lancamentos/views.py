from datetime import date

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from lancamentos.forms import CompraParceladaForm, LancamentoForm, MarcarPagoForm
from lancamentos.models import Lancamento
from meses.services import excluir_serie_futura, atualizar_serie_futura


def _erro(request, mensagem):
    if request.headers.get("HX-Request"):
        messages.error(request, mensagem)
        return HttpResponse(status=204, headers={"HX-Refresh": "true"})
    return HttpResponseBadRequest(mensagem)


def _contexto_mes(request):
    hoje = date.today()
    ano = int(request.GET.get("ano", hoje.year))
    mes = int(request.GET.get("mes", hoje.month))
    return ano, mes


@require_http_methods(["GET", "POST"])
def criar_lancamento(request):
    ano, mes = _contexto_mes(request)

    if request.method == "POST":
        form = LancamentoForm(request.POST, instance=Lancamento(competencia_ano=ano, competencia_mes=mes))
        if form.is_valid():
            form.save()
            if request.headers.get("HX-Request"):
                return HttpResponse(status=204)
            return redirect(f"/?ano={ano}&mes={mes}")
    else:
        form = LancamentoForm()

    return render(request, "lancamentos/form.html", {"form": form, "ano": ano, "mes": mes})


@require_http_methods(["POST"])
def marcar_pago(request, pk):
    lancamento = get_object_or_404(Lancamento, pk=pk)
    form = MarcarPagoForm(request.POST)
    if not form.is_valid():
        return _erro(request, "Data de pagamento invalida.")
    lancamento.data_pagamento = form.cleaned_data["data_pagamento"]
    lancamento.save(update_fields=["data_pagamento"])
    messages.success(request, "Lancamento marcado como pago.")
    return HttpResponse(status=204, headers={"HX-Refresh": "true"})


@require_http_methods(["POST"])
def excluir_lancamento(request, pk):
    lancamento = get_object_or_404(Lancamento, pk=pk)
    ignorar_par = request.POST.get("ignorar_par") == "1"

    if lancamento.lancamento_vinculado_id and not ignorar_par:
        par = lancamento.lancamento_vinculado
        return render(
            request,
            "lancamentos/_confirmar_excluir_par.html",
            {"lancamento": lancamento, "par": par},
        )

    excluir_serie_futura(lancamento)
    messages.success(request, "Lancamento excluido.")
    return HttpResponse(status=204, headers={"HX-Refresh": "true"})


@require_http_methods(["POST"])
def excluir_lancamento_par(request, pk):
    lancamento = get_object_or_404(Lancamento, pk=pk)
    par = lancamento.lancamento_vinculado
    excluir_serie_futura(lancamento)
    if par and par.pk:
        try:
            par.refresh_from_db()
            excluir_serie_futura(par)
        except Lancamento.DoesNotExist:
            pass
    messages.success(request, "Lancamentos excluidos.")
    return HttpResponse(status=204, headers={"HX-Refresh": "true"})


@require_http_methods(["GET", "POST"])
def editar_lancamento(request, pk):
    lancamento = get_object_or_404(Lancamento, pk=pk)
    encerrado = (lancamento.competencia_ano, lancamento.competencia_mes) < (date.today().year, date.today().month)

    if request.method == "POST":
        form = LancamentoForm(request.POST, instance=lancamento)
        confirmar = request.POST.get("confirmar_edicao_mes_encerrado") == "1"
        if encerrado and not confirmar:
            return HttpResponseBadRequest("Voce realmente quer editar um mes ja encerrado?")
        if form.is_valid():
            with transaction.atomic():
                atualizado = form.save(commit=False)
                campos = {
                    "descricao": atualizado.descricao,
                    "data_vencimento": atualizado.data_vencimento,
                    "valor": atualizado.valor,
                    "conta": atualizado.conta,
                    "tipo": atualizado.tipo,
                }
                atualizar_serie_futura(lancamento, **campos)
                # Save lancamento_vinculado separately — not cascaded to recurring series
                novo_vinculado = atualizado.lancamento_vinculado
                if lancamento.lancamento_vinculado != novo_vinculado:
                    lancamento.lancamento_vinculado = novo_vinculado
                    lancamento.save(update_fields=["lancamento_vinculado"])
            if request.headers.get("HX-Request"):
                messages.success(request, "Lancamento atualizado.")
                return HttpResponse(status=204, headers={"HX-Refresh": "true"})
            return redirect(f"/?ano={lancamento.competencia_ano}&mes={lancamento.competencia_mes}")
    else:
        form = LancamentoForm(instance=lancamento)

    return render(
        request,
        "lancamentos/form_edicao.html",
        {
            "form": form,
            "lancamento": lancamento,
            "encerrado": encerrado,
        },
    )


@require_http_methods(["GET", "POST"])
def criar_compra_parcelada(request):
    ano, mes = _contexto_mes(request)

    if request.method == "POST":
        form = CompraParceladaForm(request.POST)
        if form.is_valid():
            form.save()
            if request.headers.get("HX-Request"):
                return HttpResponse(status=204)
            return redirect(f"/?ano={ano}&mes={mes}")
    else:
        form = CompraParceladaForm()

    return render(request, "lancamentos/form_compra_parcelada.html", {"form": form})
