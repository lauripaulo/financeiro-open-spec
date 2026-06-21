from django import forms

from contas.models import Conta
from contas.widgets import MoedaWidget
from lancamentos.models import Lancamento
from parcelas.services import gerar_parcelas_da_compra


class LancamentoForm(forms.ModelForm):
    class Meta:
        model = Lancamento
        fields = ["descricao", "tipo", "data_vencimento", "valor", "conta"]
        widgets = {
            "valor": MoedaWidget(),
        }

    TIPOS_EXCLUIDOS_DO_CADASTRO_MANUAL = {
        Lancamento.Tipo.CONCILIACAO,
        Lancamento.Tipo.PARCELA_CARTAO,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo"].choices = [
            escolha
            for escolha in self.fields["tipo"].choices
            if escolha[0] not in self.TIPOS_EXCLUIDOS_DO_CADASTRO_MANUAL
        ]

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        conta = cleaned_data.get("conta")

        if tipo == Lancamento.Tipo.CONCILIACAO:
            self.add_error("tipo", "Conciliacao e gerada automaticamente pelo sistema.")

        if tipo == Lancamento.Tipo.PARCELA_CARTAO:
            self.add_error(
                "tipo",
                "Parcela de Cartao nao pode ser criada manualmente. Use o fluxo de compra parcelada para gerar as parcelas.",
            )

        if tipo in {Lancamento.Tipo.APORTE, Lancamento.Tipo.RESGATE} and conta and conta.tipo != Conta.Tipo.INVESTIMENTO:
            self.add_error("conta", "Aporte e Resgate sao exclusivos de contas Investimento.")

        if conta and conta.tipo == Conta.Tipo.INVESTIMENTO and tipo not in {
            Lancamento.Tipo.APORTE,
            Lancamento.Tipo.RESGATE,
        }:
            self.add_error("tipo", "Conta Investimento aceita somente Aporte e Resgate no cadastro manual.")

        return cleaned_data


class MarcarPagoForm(forms.Form):
    data_pagamento = forms.DateField()


class CompraParceladaForm(forms.Form):
    descricao = forms.CharField(max_length=180)
    valor_total = forms.DecimalField(max_digits=14, decimal_places=2, widget=MoedaWidget())
    total_parcelas = forms.IntegerField(min_value=2, max_value=120)
    conta = forms.ModelChoiceField(queryset=Conta.objects.filter(tipo=Conta.Tipo.CARTAO).order_by("nome"))
    data_compra = forms.DateField()

    def save(self):
        return gerar_parcelas_da_compra(
            descricao=self.cleaned_data["descricao"],
            valor_total=self.cleaned_data["valor_total"],
            total_parcelas=self.cleaned_data["total_parcelas"],
            conta=self.cleaned_data["conta"],
            data_compra=self.cleaned_data["data_compra"],
        )
