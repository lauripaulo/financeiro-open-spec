from decimal import Decimal

from django import forms

from contas.models import Conta
from contas.widgets import MoedaWidget
from lancamentos.models import Lancamento
from lancamentos.services import gerar_transferencia
from parcelas.services import gerar_parcelas_da_compra


class ContaSelect(forms.Select):
    """Select de conta que expoe o tipo da conta em cada option, para o filtro
    tipo->conta feito em conditional-fields.js."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        instance = getattr(value, "instance", None)
        if instance is not None:
            option["attrs"]["data-conta-tipo"] = instance.tipo
        return option


class LancamentoForm(forms.ModelForm):
    class Meta:
        model = Lancamento
        fields = ["descricao", "tipo", "data_vencimento", "valor", "conta"]
        widgets = {
            "valor": MoedaWidget(),
            "data_vencimento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "conta": ContaSelect(),
        }

    TIPOS_EXCLUIDOS_DO_CADASTRO_MANUAL = {
        Lancamento.Tipo.CONCILIACAO,
        Lancamento.Tipo.PARCELA_CARTAO,
        Lancamento.Tipo.TRANSFERENCIA_ENVIADA,
        Lancamento.Tipo.TRANSFERENCIA_RECEBIDA,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        excluidos = self.TIPOS_EXCLUIDOS_DO_CADASTRO_MANUAL.copy()
        if self.instance.pk and self.instance.tipo in excluidos:
            excluidos.remove(self.instance.tipo)
            self.fields["tipo"].disabled = True

        self.fields["tipo"].choices = [
            escolha
            for escolha in self.fields["tipo"].choices
            if escolha[0] not in excluidos
        ]

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        conta = cleaned_data.get("conta")

        if not self.instance.pk:
            if tipo == Lancamento.Tipo.CONCILIACAO:
                self.add_error("tipo", "Conciliacao e gerada automaticamente pelo sistema.")

            if tipo == Lancamento.Tipo.PARCELA_CARTAO:
                self.add_error(
                    "tipo",
                    "Parcela de Cartao nao pode ser criada manualmente. Use o fluxo de compra parcelada para gerar as parcelas.",
                )

            if tipo in {Lancamento.Tipo.TRANSFERENCIA_ENVIADA, Lancamento.Tipo.TRANSFERENCIA_RECEBIDA}:
                self.add_error(
                    "tipo",
                    "Transferencia nao pode ser criada manualmente. Use o fluxo de transferencia entre contas.",
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
    data_pagamento = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))


class CompraParceladaForm(forms.Form):
    descricao = forms.CharField(max_length=180)
    valor_total = forms.DecimalField(max_digits=14, decimal_places=2, widget=MoedaWidget())
    total_parcelas = forms.IntegerField(min_value=2, max_value=120)
    parcelas_pagas = forms.IntegerField(min_value=0, initial=0)
    conta = forms.ModelChoiceField(queryset=Conta.objects.filter(tipo=Conta.Tipo.CARTAO).order_by("nome"))
    data_compra = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))

    def clean(self):
        cleaned_data = super().clean()
        total_parcelas = cleaned_data.get("total_parcelas")
        parcelas_pagas = cleaned_data.get("parcelas_pagas")

        if total_parcelas is None or parcelas_pagas is None:
            return cleaned_data

        if parcelas_pagas > total_parcelas:
            self.add_error("parcelas_pagas", "Parcelas pagas nao pode ser maior que o total de parcelas.")

        if parcelas_pagas == total_parcelas:
            self.add_error("parcelas_pagas", "Nao ha parcelas a gerar para esta compra.")

        return cleaned_data

    def save(self):
        return gerar_parcelas_da_compra(
            descricao=self.cleaned_data["descricao"],
            valor_total=self.cleaned_data["valor_total"],
            total_parcelas=self.cleaned_data["total_parcelas"],
            parcelas_pagas=self.cleaned_data["parcelas_pagas"],
            conta=self.cleaned_data["conta"],
            data_compra=self.cleaned_data["data_compra"],
        )


class TransferenciaForm(forms.Form):
    CONTAS_PERMITIDAS = (Conta.Tipo.BANCO, Conta.Tipo.CARTAO)

    descricao = forms.CharField(max_length=180)
    conta_origem = forms.ModelChoiceField(queryset=Conta.objects.none(), label="Conta de origem")
    conta_destino = forms.ModelChoiceField(queryset=Conta.objects.none(), label="Conta de destino")
    valor = forms.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"), widget=MoedaWidget())
    data_vencimento = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        contas = Conta.objects.filter(tipo__in=self.CONTAS_PERMITIDAS).order_by("nome")
        self.fields["conta_origem"].queryset = contas
        self.fields["conta_destino"].queryset = contas

    def clean(self):
        cleaned_data = super().clean()
        conta_origem = cleaned_data.get("conta_origem")
        conta_destino = cleaned_data.get("conta_destino")

        if conta_origem and conta_destino and conta_origem == conta_destino:
            self.add_error("conta_destino", "Conta de destino deve ser diferente da conta de origem.")

        return cleaned_data

    def save(self):
        return gerar_transferencia(
            descricao=self.cleaned_data["descricao"],
            conta_origem=self.cleaned_data["conta_origem"],
            conta_destino=self.cleaned_data["conta_destino"],
            valor=self.cleaned_data["valor"],
            data_vencimento=self.cleaned_data["data_vencimento"],
        )
