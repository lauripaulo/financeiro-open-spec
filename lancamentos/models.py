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
        TRANSFERENCIA_ENVIADA = "TRANSFERENCIA_ENVIADA", "Transferencia Enviada"
        TRANSFERENCIA_RECEBIDA = "TRANSFERENCIA_RECEBIDA", "Transferencia Recebida"

    class Status(models.TextChoices):
        PREVISTO = "PREVISTO", "Previsto"
        PENDENTE = "PENDENTE", "Pendente"
        PAGO = "PAGO", "Pago"

    TIPOS_PROPAGAVEIS = {
        Tipo.RECEBIMENTO_FIXO,
        Tipo.GASTO_FIXO,
        Tipo.ASSINATURA,
    }

    TIPOS_INVESTIMENTO = {
        Tipo.APORTE,
        Tipo.RESGATE,
    }

    TIPOS_ENTRADA = {
        Tipo.RECEBIMENTO_FIXO,
        Tipo.RECEBIMENTO_EXCEPCIONAL,
        Tipo.APORTE,
        Tipo.TRANSFERENCIA_RECEBIDA,
    }

    TIPOS_SAIDA = {
        Tipo.GASTO_FIXO,
        Tipo.GASTO_VARIAVEL,
        Tipo.ASSINATURA,
        Tipo.PARCELA_CARTAO,
        Tipo.RESGATE,
        Tipo.TRANSFERENCIA_ENVIADA,
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
    lancamento_vinculado = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lancamento_par",
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
        conta_tipo = None

        if not 1 <= self.competencia_mes <= 12:
            errors["competencia_mes"] = "Mes de competencia deve estar entre 1 e 12."

        if self.conta_id is not None:
            try:
                conta_tipo = self.conta.tipo
            except Conta.DoesNotExist:
                errors["conta"] = "Conta informada nao encontrada."
        if self.tipo == self.Tipo.CONCILIACAO and not self.gerado_automaticamente:
            errors["tipo"] = "Conciliacao e criada apenas automaticamente pelo sistema."

        if conta_tipo is not None and self.tipo in self.TIPOS_INVESTIMENTO and conta_tipo != Conta.Tipo.INVESTIMENTO:
            errors["tipo"] = "Aporte e Resgate sao exclusivos de contas Investimento."

        if conta_tipo == Conta.Tipo.INVESTIMENTO and self.tipo not in (
            self.TIPOS_INVESTIMENTO | {self.Tipo.CONCILIACAO}
        ):
            errors["tipo"] = "Conta Investimento aceita apenas Aporte, Resgate e Conciliacao automatica."

        if self.tipo == self.Tipo.PARCELA_CARTAO:
            if conta_tipo != Conta.Tipo.CARTAO:
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

        if self.lancamento_vinculado_id is not None:
            if self.pk and self.lancamento_vinculado_id == self.pk:
                errors["lancamento_vinculado"] = "Um lancamento nao pode ser vinculado a si mesmo."
            elif self.valor is not None:
                try:
                    par = Lancamento.objects.get(pk=self.lancamento_vinculado_id)
                    if abs(self.valor) != abs(par.valor):
                        errors["lancamento_vinculado"] = (
                            f"O valor do lancamento vinculado (R$ {abs(par.valor)}) deve ser "
                            f"igual ao valor deste lancamento (R$ {abs(self.valor)})."
                        )
                except Lancamento.DoesNotExist:
                    errors["lancamento_vinculado"] = "Lancamento vinculado nao encontrado."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Track previous lancamento_vinculado for cleanup before saving
        old_vinculado_id = None
        if self.pk:
            old_vinculado_id = (
                Lancamento.objects.filter(pk=self.pk)
                .values_list("lancamento_vinculado_id", flat=True)
                .first()
            )

        self.full_clean()
        resultado = super().save(*args, **kwargs)
        if self.is_recorrente and self.grupo_recorrencia_id is None:
            self.grupo_recorrencia = self
            super().save(update_fields=["grupo_recorrencia"])

        # Sync lancamento_vinculado bidirectionally using queryset.update() to
        # avoid triggering full_clean() recursively on the other side.
        new_vinculado_id = self.lancamento_vinculado_id
        if old_vinculado_id != new_vinculado_id:
            # Clear old link if the old partner was pointing back at this instance
            if old_vinculado_id is not None:
                Lancamento.objects.filter(
                    pk=old_vinculado_id, lancamento_vinculado_id=self.pk
                ).update(lancamento_vinculado=None)

            # Set new reverse link (cycle guard: skip if partner already points here)
            if new_vinculado_id is not None:
                parceiro_antigo_id = (
                    Lancamento.objects.filter(pk=new_vinculado_id)
                    .values_list("lancamento_vinculado_id", flat=True)
                    .first()
                )
                if parceiro_antigo_id is not None and parceiro_antigo_id != self.pk:
                    Lancamento.objects.filter(
                        pk=parceiro_antigo_id, lancamento_vinculado_id=new_vinculado_id
                    ).update(lancamento_vinculado=None)

                Lancamento.objects.filter(pk=new_vinculado_id).exclude(
                    lancamento_vinculado_id=self.pk
                ).update(lancamento_vinculado=self.pk)

        return resultado
