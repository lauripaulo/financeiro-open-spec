from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from importacao.forms import ImportacaoOFXNubankCartaoForm, ImportacaoOFXNubankContaForm
from importacao.services import importar_ofx_nubank_cartao, importar_ofx_nubank_conta

SESSAO_RESUMO = "importacao_resumo"


@require_http_methods(["GET"])
def index(request):
    return render(request, "importacao/index.html")


def _processar_importacao(request, *, form_class, servico, titulo, ajuda):
    if request.method == "POST":
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            try:
                resumo = servico(
                    conta=form.cleaned_data["conta"],
                    texto=form.cleaned_data["texto"],
                    modo=form.cleaned_data["modo"],
                )
            except ValidationError as exc:
                form.add_error(None, " ".join(exc.messages))
            else:
                resumo["conta"] = form.cleaned_data["conta"].nome
                request.session[SESSAO_RESUMO] = resumo
                return redirect("importacao:resultado")
    else:
        form = form_class()

    return render(
        request,
        "importacao/ofx_form.html",
        {"form": form, "titulo": titulo, "ajuda": ajuda, "voltar_url": reverse("importacao:index")},
    )


@require_http_methods(["GET", "POST"])
def importar_nubank_cartao(request):
    return _processar_importacao(
        request,
        form_class=ImportacaoOFXNubankCartaoForm,
        servico=importar_ofx_nubank_cartao,
        titulo="Importar OFX do cartao Nubank",
        ajuda=(
            "Envie o extrato OFX da fatura. Compras parceladas geram as parcelas "
            "futuras como projecao; importacoes seguintes podem corrigi-las."
        ),
    )


@require_http_methods(["GET", "POST"])
def importar_nubank_conta(request):
    return _processar_importacao(
        request,
        form_class=ImportacaoOFXNubankContaForm,
        servico=importar_ofx_nubank_conta,
        titulo="Importar OFX da conta Nubank",
        ajuda=(
            "Envie o extrato OFX da conta corrente. Cada transacao vira um "
            "lancamento ja pago na data em que ocorreu; o pagamento de fatura "
            "do cartao e pulado para nao duplicar gastos."
        ),
    )


@require_http_methods(["GET"])
def resultado(request):
    resumo = request.session.pop(SESSAO_RESUMO, None)
    if resumo is None:
        return redirect("importacao:index")

    return render(request, "importacao/resultado.html", {"resumo": resumo})
