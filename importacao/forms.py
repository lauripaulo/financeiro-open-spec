from django import forms

from contas.models import Conta
from importacao.services import MODO_NOVOS, MODO_SOBRESCREVER


class ImportacaoOFXNubankCartaoForm(forms.Form):
    MODO_CHOICES = [
        (MODO_NOVOS, "Somente itens novos"),
        (MODO_SOBRESCREVER, "Sobrescrever existentes (corrige projecoes nao pagas)"),
    ]

    arquivo = forms.FileField(label="Arquivo OFX")
    conta = forms.ModelChoiceField(
        label="Conta do cartao",
        queryset=Conta.objects.filter(tipo=Conta.Tipo.CARTAO),
        empty_label="Selecione o cartao",
    )
    modo = forms.ChoiceField(
        label="Modo de importacao",
        choices=MODO_CHOICES,
        initial=MODO_NOVOS,
        widget=forms.RadioSelect,
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        conteudo = arquivo.read()
        try:
            texto = conteudo.decode("utf-8")
        except UnicodeDecodeError:
            texto = conteudo.decode("cp1252")
        self.cleaned_data["texto"] = texto
        return arquivo
