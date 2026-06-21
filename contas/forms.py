from django import forms

from contas.models import Conta
from contas.widgets import MoedaWidget


class ContaForm(forms.ModelForm):
    class Meta:
        model = Conta
        fields = ["nome", "tipo", "dia_vencimento", "saldo_atual", "limite_negativo"]
        widgets = {
            "saldo_atual": MoedaWidget(),
            "limite_negativo": MoedaWidget(),
        }
