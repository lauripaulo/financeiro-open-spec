from django import forms

from contas.models import Conta
from importacao.services import MODO_NOVOS, MODO_SOBRESCREVER


class _ImportacaoOFXFormBase(forms.Form):
    MODO_CHOICES = [
        (MODO_NOVOS, "Somente itens novos"),
        (MODO_SOBRESCREVER, "Sobrescrever existentes (corrige projecoes nao pagas)"),
    ]

    arquivo = forms.FileField(label="Arquivo OFX")
    modo = forms.ChoiceField(
        label="Modo de importacao",
        choices=MODO_CHOICES,
        initial=MODO_NOVOS,
        widget=forms.RadioSelect,
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        conteudo = arquivo.read()
        for encoding in ("utf-8", "cp1252"):
            try:
                texto = conteudo.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise forms.ValidationError(
                "Arquivo nao pode ser lido como texto (esperado OFX em UTF-8 ou CP1252)."
            )
        self.cleaned_data["texto"] = texto
        return arquivo


class ImportacaoOFXNubankCartaoForm(_ImportacaoOFXFormBase):
    conta = forms.ModelChoiceField(
        label="Conta do cartao",
        queryset=Conta.objects.filter(tipo=Conta.Tipo.CARTAO),
        empty_label="Selecione o cartao",
    )


class ImportacaoOFXNubankContaForm(_ImportacaoOFXFormBase):
    conta = forms.ModelChoiceField(
        label="Conta corrente",
        queryset=Conta.objects.filter(tipo=Conta.Tipo.BANCO),
        empty_label="Selecione a conta",
    )
