from django import forms

from contas.models import Conta
from contas.widgets import MoedaWidget
from lancamentos.models import Lancamento
from parcelas.services import gerar_parcelas_da_compra


class LancamentoForm(forms.ModelForm):
    class Meta:
        model = Lancamento
        fields = ["descricao", "tipo", "data_vencimento", "valor", "conta", "lancamento_vinculado"]
        widgets = {
            "valor": MoedaWidget(),
            "data_vencimento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
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
        self.fields["lancamento_vinculado"].required = False
        self.fields["lancamento_vinculado"].empty_label = "Nenhum"
        self.fields["lancamento_vinculado"].label = "Lancamento vinculado"
        # Exclude self to prevent self-link; restrict to lancamentos ainda nao vinculados
        base_qs = Lancamento.objects.order_by("-competencia_ano", "-competencia_mes", "-data_vencimento", "descricao")
        if self.instance.pk:
            base_qs = base_qs.exclude(pk=self.instance.pk)

        ids_disponiveis = list(
            base_qs.filter(lancamento_vinculado__isnull=True).values_list("pk", flat=True)
        )
        if self.instance.lancamento_vinculado_id:
            ids_disponiveis.append(self.instance.lancamento_vinculado_id)

        self.fields["lancamento_vinculado"].queryset = base_qs.filter(pk__in=ids_disponiveis)

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        conta = cleaned_data.get("conta")
        valor = cleaned_data.get("valor")
        lancamento_vinculado = cleaned_data.get("lancamento_vinculado")

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

        if lancamento_vinculado and valor is not None:
            if abs(valor) != abs(lancamento_vinculado.valor):
                self.add_error(
                    "lancamento_vinculado",
                    f"O valor do lancamento vinculado (R$ {abs(lancamento_vinculado.valor)}) deve ser "
                    f"igual ao valor deste lancamento (R$ {abs(valor)}).",
                )

        return cleaned_data


class MarcarPagoForm(forms.Form):
    data_pagamento = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))


class CompraParceladaForm(forms.Form):
    descricao = forms.CharField(max_length=180)
    valor_total = forms.DecimalField(max_digits=14, decimal_places=2, widget=MoedaWidget())
    total_parcelas = forms.IntegerField(min_value=2, max_value=120)
    conta = forms.ModelChoiceField(queryset=Conta.objects.filter(tipo=Conta.Tipo.CARTAO).order_by("nome"))
    data_compra = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))

    def save(self):
        return gerar_parcelas_da_compra(
            descricao=self.cleaned_data["descricao"],
            valor_total=self.cleaned_data["valor_total"],
            total_parcelas=self.cleaned_data["total_parcelas"],
            conta=self.cleaned_data["conta"],
            data_compra=self.cleaned_data["data_compra"],
        )
