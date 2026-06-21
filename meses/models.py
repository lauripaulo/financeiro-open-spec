from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from contas.models import Conta


class MesAberto(models.Model):
    ano = models.PositiveIntegerField()
    mes = models.PositiveSmallIntegerField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ano", "mes"]
        constraints = [
            models.UniqueConstraint(fields=["ano", "mes"], name="mes_aberto_unico"),
        ]

    def __str__(self):
        return f"{self.mes:02d}/{self.ano}"

    def clean(self):
        if not 1 <= self.mes <= 12:
            raise ValidationError({"mes": "Mes deve estar entre 1 e 12."})


class SaldoMensalConta(models.Model):
    conta = models.ForeignKey(Conta, on_delete=models.PROTECT, related_name="saldos_mensais")
    ano = models.PositiveIntegerField()
    mes = models.PositiveSmallIntegerField()
    saldo_inicial = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ano", "mes", "conta_id"]
        constraints = [
            models.UniqueConstraint(fields=["conta", "ano", "mes"], name="saldo_mensal_conta_unico"),
        ]

    def __str__(self):
        return f"{self.conta} - {self.mes:02d}/{self.ano}"

    def clean(self):
        if not 1 <= self.mes <= 12:
            raise ValidationError({"mes": "Mes deve estar entre 1 e 12."})
