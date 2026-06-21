from decimal import Decimal

from django import forms


class MoedaWidget(forms.TextInput):
    """Widget de texto para campos monetarios, com mascara BRL aplicada via JS.

    O valor inicial e renderizado ja formatado (256.432,11). O envio ao
    servidor continua em decimal puro, pois o JS reescreve o campo antes do
    submit (ver static/js/money-mask.js).
    """

    def __init__(self, attrs=None):
        default_attrs = {
            "class": "money-input",
            "inputmode": "decimal",
            "autocomplete": "off",
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def format_value(self, value):
        if value is None or value == "":
            return ""
        try:
            valor = Decimal(value)
        except (ArithmeticError, TypeError, ValueError):
            return value

        negativo = valor < 0
        valor = abs(valor).quantize(Decimal("0.01"))
        inteiro, _, decimal = f"{valor:.2f}".partition(".")

        grupos = []
        while len(inteiro) > 3:
            grupos.insert(0, inteiro[-3:])
            inteiro = inteiro[:-3]
        grupos.insert(0, inteiro)
        inteiro_formatado = ".".join(grupos)

        sinal = "-" if negativo else ""
        return f"{sinal}{inteiro_formatado},{decimal}"
