from django.db import models

from contas.models import Conta
from lancamentos.models import Lancamento
from parcelas.models import CompraParcelada


class ItemImportado(models.Model):
    conta = models.ForeignKey(Conta, on_delete=models.PROTECT, related_name="itens_importados")
    fitid = models.CharField(max_length=255)
    chave_dedup = models.CharField(max_length=64, unique=True)
    lancamento = models.ForeignKey(
        Lancamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="itens_importados",
    )
    compra = models.ForeignKey(
        CompraParcelada,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="itens_importados",
    )
    acctid = models.CharField(max_length=255, blank=True)
    importado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-importado_em", "-id"]
        verbose_name = "Item importado"
        verbose_name_plural = "Itens importados"

    def __str__(self):
        return f"{self.fitid} ({self.conta})"
