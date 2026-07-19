from django import forms


class ContaSelect(forms.Select):
    """Select de conta que expoe o tipo da conta em cada option, para o filtro
    tipo->conta feito em conditional-fields.js."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        instance = getattr(value, "instance", None)
        if instance is not None:
            option["attrs"]["data-conta-tipo"] = instance.tipo
        return option
