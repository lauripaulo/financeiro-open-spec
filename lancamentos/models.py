from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from contas.models import Conta


class LancamentoQuerySet(models.QuerySet):
    def pagos(self):
        return self.filter(data_pagamento__isnull=False)

    def previstos(self):
        hoje = timezone.localdate()
        return self.filter(data_pagamento__isnull=True, data_vencimento__gte=hoje)

    def pendentes(self):
        hoje = timezone.localdate()
        return self.filter(data_pagamento__isnull=True, data_vencimento__lt=hoje)

    def com_status(self, status):
        status = status.upper()
        if status == Lancamento.Status.PAGO:
            return self.pagos()
        if status == Lancamento.Status.PREVISTO:
            return self.previstos()
        if status == Lancamento.Status.PENDENTE:
            return self.pendentes()
        raise ValueError(f"Status invalido: {status}")

    def com_status_in(self, status_list):
        if not status_list:
            return self

        hoje = timezone.localdate()
        condicoes = models.Q(pk__in=[])
        for status in {s.upper() for s in status_list}:
            if status == Lancamento.Status.PAGO:
                condicoes |= models.Q(data_pagamento__isnull=False)
            elif status == Lancamento.Status.PREVISTO:
                condicoes |= models.Q(data_pagamento__isnull=True, data_vencimento__gte=hoje)
            elif status == Lancamento.Status.PENDENTE:
                condicoes |= models.Q(data_pagamento__isnull=True, data_vencimento__lt=hoje)
            else:
                raise ValueError(f"Status invalido: {status}")

        return self.filter(condicoes)


class Lancamento(models.Model):
    class Tipo(models.TextChoices):
        RECEBIMENTO_FIXO = "RECEBIMENTO_FIXO", "Recebimento Fixo"
        RECEBIMENTO_EXCEPCIONAL = "RECEBIMENTO_EXCEPCIONAL", "Recebimento Excepcional"
        GASTO_FIXO = "GASTO_FIXO", "Gasto Fixo"
        GASTO_VARIAVEL = "GASTO_VARIAVEL", "Gasto Variavel"
        ASSINATURA = "ASSINATURA", "Assinatura"
        PARCELA_CARTAO = "PARCELA_CARTAO", "Parcela de Cartao"
        CONCILIACAO = "CONCILIACAO", "Conciliacao"
        APORTE = "APORTE", "Aporte"
        RESGATE = "RESGATE", "Resgate"

    class Status(models.TextChoices):
        PREVISTO = "PREVISTO", "Previsto"
        PENDENTE = "PENDENTE", "Pendente"
        PAGO = "PAGO", "Pago"

    TIPOS_PROPAGAVEIS = {
        Tipo.RECEBIMENTO_FIXO,
        Tipo.GASTO_FIXO,
        Tipo.ASSINATURA,
        Tipo.PARCELA_CARTAO,
    }

    TIPOS_ENTRADA = {
        Tipo.RECEBIMENTO_FIXO,
        Tipo.RECEBIMENTO_EXCEPCIONAL,
        Tipo.APORTE,
    }

    TIPOS_SAIDA = {
        Tipo.GASTO_FIXO,
        Tipo.GASTO_VARIAVEL,
        Tipo.ASSINATURA,
        Tipo.PARCELA_CARTAO,
        Tipo.RESGATE,
    }

    descricao = models.CharField(max_length=180)
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    data_vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    conta = models.ForeignKey(Conta, on_delete=models.PROTECT, related_name="lancamentos")
    competencia_ano = models.PositiveIntegerField()
    competencia_mes = models.PositiveSmallIntegerField()
    grupo_recorrencia = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instancias_recorrentes",
    )
    total_parcelas = models.PositiveSmallIntegerField(null=True, blank=True)
    parcela_atual = models.PositiveSmallIntegerField(null=True, blank=True)
    gerado_automaticamente = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    objects = LancamentoQuerySet.as_manager()

    class Meta:
        ordering = ["competencia_ano", "competencia_mes", "data_vencimento", "id"]

    def __str__(self):
        return f"{self.descricao} ({self.competencia_mes:02d}/{self.competencia_ano})"

    @property
    def status(self):
        if self.data_pagamento:
            return self.Status.PAGO
        if self.data_vencimento < timezone.localdate():
            return self.Status.PENDENTE
        return self.Status.PREVISTO

    @property
    def direcao(self):
        if self.tipo == self.Tipo.CONCILIACAO:
            return "ENTRADA" if self.valor >= Decimal("0") else "SAIDA"
        if self.tipo in self.TIPOS_ENTRADA:
            return "ENTRADA"
        if self.tipo in self.TIPOS_SAIDA:
            return "SAIDA"
        raise ValueError(f"Tipo nao suportado: {self.tipo}")

    @property
    def valor_absoluto(self):
        return abs(self.valor)

    @property
    def is_recorrente(self):
        return self.tipo in self.TIPOS_PROPAGAVEIS

    def clean(self):
        errors = {}

        if not 1 <= self.competencia_mes <= 12:
            errors["competencia_mes"] = "Mes de competencia deve estar entre 1 e 12."

        if self.tipo == self.Tipo.CONCILIACAO and not self.gerado_automaticamente:
            errors["tipo"] = "Conciliacao e criada apenas automaticamente pelo sistema."

        if self.tipo in {self.Tipo.APORTE, self.Tipo.RESGATE} and self.conta.tipo != Conta.Tipo.INVESTIMENTO:
            errors["tipo"] = "Aporte e Resgate sao exclusivos de contas Investimento."

        if self.conta.tipo == Conta.Tipo.INVESTIMENTO and self.tipo not in {
            self.Tipo.APORTE,
            self.Tipo.RESGATE,
            self.Tipo.CONCILIACAO,
        }:
            errors["tipo"] = "Conta Investimento aceita apenas Aporte, Resgate e Conciliacao automatica."

        if self.tipo == self.Tipo.PARCELA_CARTAO:
            if self.conta.tipo != Conta.Tipo.CARTAO:
                errors["conta"] = "Parcela de Cartao exige conta do tipo Cartao."
            if not self.total_parcelas or not self.parcela_atual:
                errors["total_parcelas"] = "Parcela de Cartao exige total_parcelas e parcela_atual."
            elif self.parcela_atual > self.total_parcelas:
                errors["parcela_atual"] = "Parcela atual nao pode exceder total_parcelas."
        else:
            if self.total_parcelas is not None or self.parcela_atual is not None:
                errors["total_parcelas"] = "Campos de parcela sao exclusivos para tipo Parcela de Cartao."

        if self.valor == Decimal("0"):
            errors["valor"] = "Valor nao pode ser zero."

        if self.tipo != self.Tipo.CONCILIACAO and self.valor < Decimal("0"):
            errors["valor"] = "Valor deve ser positivo para tipos diferentes de Conciliacao."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        resultado = super().save(*args, **kwargs)
        if self.is_recorrente and self.grupo_recorrencia_id is None:
            self.grupo_recorrencia = self
            super().save(update_fields=["grupo_recorrencia"])
        return resultado
