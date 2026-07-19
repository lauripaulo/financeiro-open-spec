from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from importacao.forms import ImportacaoOFXNubankCartaoForm
from importacao.services import importar_ofx_nubank_cartao

SESSAO_RESUMO = "importacao_resumo"


@require_http_methods(["GET"])
def index(request):
    return render(request, "importacao/index.html")


@require_http_methods(["GET", "POST"])
def importar_nubank_cartao(request):
    if request.method == "POST":
        form = ImportacaoOFXNubankCartaoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                resumo = importar_ofx_nubank_cartao(
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
        form = ImportacaoOFXNubankCartaoForm()

    return render(request, "importacao/nubank_cartao_form.html", {"form": form})


@require_http_methods(["GET"])
def resultado(request):
    resumo = request.session.pop(SESSAO_RESUMO, None)
    if resumo is None:
        return redirect("importacao:index")

    return render(request, "importacao/resultado.html", {"resumo": resumo})
