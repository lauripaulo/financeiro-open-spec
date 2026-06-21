from django import forms

from contas.models import Conta


class ContaForm(forms.ModelForm):
    class Meta:
        model = Conta
        fields = ["nome", "tipo", "dia_vencimento", "saldo_atual", "limite_negativo"]
