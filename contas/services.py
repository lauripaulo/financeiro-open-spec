from decimal import Decimal


def validar_limite_negativo(limite_negativo):
    """Retorna mensagem de erro se limite_negativo for negativo."""
    if limite_negativo is not None and limite_negativo < 0:
        return "Informe o limite negativo como valor positivo."
    return None
