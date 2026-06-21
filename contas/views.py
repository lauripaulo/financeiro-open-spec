from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from contas.forms import ContaForm
from contas.models import Conta


@require_http_methods(["GET"])
def listar_contas(request):
    return render(request, "contas/lista.html", {"contas": Conta.objects.all()})


@require_http_methods(["GET", "POST"])
def criar_conta(request):
    if request.method == "POST":
        form = ContaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("contas:listar")
    else:
        form = ContaForm()

    return render(request, "contas/form.html", {"form": form})


@require_http_methods(["GET", "POST"])
def editar_conta(request, pk):
    conta = get_object_or_404(Conta, pk=pk)

    if request.method == "POST":
        form = ContaForm(request.POST, instance=conta)
        if form.is_valid():
            form.save()
            return redirect("contas:listar")
    else:
        form = ContaForm(instance=conta)

    return render(request, "contas/form.html", {"form": form, "conta": conta})


@require_http_methods(["POST"])
def excluir_conta(request, pk):
    conta = get_object_or_404(Conta, pk=pk)
    erro = None
    try:
        conta.delete()
    except ValidationError as exc:
        erro = " ".join(exc.messages)

    return render(request, "contas/lista.html", {"contas": Conta.objects.all(), "erro_exclusao": erro})
