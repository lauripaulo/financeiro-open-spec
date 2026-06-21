from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class Conta(models.Model):
    class Tipo(models.TextChoices):
        CARTAO = "CARTAO", "Cartao"
        BANCO = "BANCO", "Banco"
        INVESTIMENTO = "INVESTIMENTO", "Investimento"

    nome = models.CharField(max_length=120, unique=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    dia_vencimento = models.PositiveSmallIntegerField(null=True, blank=True)
    saldo_atual = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    limite_negativo = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Limite negativo de referencia para alerta.",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def clean(self):
        errors = {}

        if self.tipo == self.Tipo.CARTAO:
            if not self.dia_vencimento:
                errors["dia_vencimento"] = "Cartao exige dia de vencimento."
            if self.saldo_atual is not None:
                errors["saldo_atual"] = "Cartao nao usa saldo inicial."
            if self.limite_negativo is not None:
                errors["limite_negativo"] = "Cartao nao usa limite negativo."

        if self.tipo == self.Tipo.BANCO:
            if self.saldo_atual is None:
                errors["saldo_atual"] = "Banco exige saldo inicial."
            if self.dia_vencimento:
                errors["dia_vencimento"] = "Banco nao usa dia de vencimento."

        if self.tipo == self.Tipo.INVESTIMENTO:
            if self.saldo_atual is None:
                errors["saldo_atual"] = "Investimento exige saldo inicial."
            if self.dia_vencimento:
                errors["dia_vencimento"] = "Investimento nao usa dia de vencimento."
            if self.limite_negativo is not None:
                errors["limite_negativo"] = "Investimento nao usa limite negativo."

        if self.dia_vencimento and not 1 <= self.dia_vencimento <= 31:
            errors["dia_vencimento"] = "Dia de vencimento deve estar entre 1 e 31."

        if self.saldo_atual is not None and self.saldo_atual.quantize(Decimal("0.01")) != self.saldo_atual:
            errors["saldo_atual"] = "Saldo atual deve ter duas casas decimais."

        if errors:
            raise ValidationError(errors)

    def delete(self, using=None, keep_parents=False):
        if self.lancamentos.exists():
            raise ValidationError("Conta com lancamentos associados nao pode ser excluida.")
        return super().delete(using=using, keep_parents=keep_parents)

    def limite_negativo_ultrapassado(self, saldo: Decimal) -> bool:
        if self.tipo != self.Tipo.BANCO or self.limite_negativo is None:
            return False
        return saldo < (self.limite_negativo * Decimal("-1"))

    def limite_negativo_proximo(self, saldo: Decimal, margem: Decimal = Decimal("50.00")) -> bool:
        if self.tipo != self.Tipo.BANCO or self.limite_negativo is None:
            return False
        limite = self.limite_negativo * Decimal("-1")
        return limite <= saldo <= (limite + margem)
