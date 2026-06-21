from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


def _formatar_brl(valor):
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
    return f"{sinal}R$ {inteiro_formatado},{decimal}"


@register.filter(name="moeda")
def moeda(valor):
    """Formata um valor monetario no padrao brasileiro: R$ 1.234,56"""
    if valor is None or valor == "":
        return "R$ 0,00"

    try:
        valor = Decimal(valor)
    except (InvalidOperation, TypeError, ValueError):
        return ""

    return _formatar_brl(valor)
