from django import template

register = template.Library()


@register.filter(name="partes_descricao")
def partes_descricao(descricao):
    """Divide no primeiro " - ": ["operacao", "contraparte"] ou ["descricao"]."""
    return [parte.strip() for parte in str(descricao).split(" - ", 1)]
