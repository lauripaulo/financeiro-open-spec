from django import forms

from contas.models import Conta
from contas.services import validar_limite_negativo
from contas.widgets import MoedaWidget


class ContaForm(forms.ModelForm):
    class Meta:
        model = Conta
        fields = ["nome", "tipo", "dia_vencimento", "saldo_atual", "limite_negativo"]
        widgets = {
            "saldo_atual": MoedaWidget(),
            "limite_negativo": MoedaWidget(),
        }

    def clean(self):
        cleaned_data = super().clean()
        limite_negativo = cleaned_data.get("limite_negativo")
        erro = validar_limite_negativo(limite_negativo)
        if erro:
            self.add_error("limite_negativo", erro)
        return cleaned_data

