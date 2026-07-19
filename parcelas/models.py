from django.core.exceptions import ValidationError
from django.db import models

from contas.models import Conta


class CompraParcelada(models.Model):
    descricao = models.CharField(max_length=180)
    conta = models.ForeignKey(Conta, on_delete=models.PROTECT, related_name="compras_parceladas")
    valor_total = models.DecimalField(max_digits=14, decimal_places=2)
    total_parcelas = models.PositiveSmallIntegerField()
    data_compra = models.DateField()
    fitid = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        help_text="Identificador da compra no banco de origem (importacao OFX).",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data_compra", "-id"]

    def __str__(self):
        return f"{self.descricao} ({self.total_parcelas}x)"

    def clean(self):
        errors = {}

        if self.conta.tipo != Conta.Tipo.CARTAO:
            errors["conta"] = "Compra parcelada exige conta do tipo Cartao."

        if self.total_parcelas < 2:
            errors["total_parcelas"] = "Compra parcelada exige ao menos 2 parcelas."

        if errors:
            raise ValidationError(errors)

    @property
    def valor_parcela(self):
        return self.valor_total / self.total_parcelas
