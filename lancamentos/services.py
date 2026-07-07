from django.core.exceptions import ValidationError
from django.db import transaction

from contas.models import Conta
from lancamentos.models import Lancamento


@transaction.atomic
def gerar_transferencia(*, conta_origem, conta_destino, valor, data_vencimento, descricao):
    if conta_origem == conta_destino:
        raise ValidationError({"conta_destino": "Conta de destino deve ser diferente da conta de origem."})

    for campo, conta in (("conta_origem", conta_origem), ("conta_destino", conta_destino)):
        if conta.tipo == Conta.Tipo.INVESTIMENTO:
            raise ValidationError({campo: "Conta Investimento nao participa de transferencias. Use Aporte/Resgate."})

    enviada = Lancamento.objects.create(
        descricao=descricao,
        tipo=Lancamento.Tipo.TRANSFERENCIA_ENVIADA,
        data_vencimento=data_vencimento,
        valor=valor,
        conta=conta_origem,
        competencia_ano=data_vencimento.year,
        competencia_mes=data_vencimento.month,
        gerado_automaticamente=True,
    )
    recebida = Lancamento.objects.create(
        descricao=descricao,
        tipo=Lancamento.Tipo.TRANSFERENCIA_RECEBIDA,
        data_vencimento=data_vencimento,
        valor=valor,
        conta=conta_destino,
        competencia_ano=data_vencimento.year,
        competencia_mes=data_vencimento.month,
        gerado_automaticamente=True,
        lancamento_vinculado=enviada,
    )
    # O save() do model sincroniza o lado reverso do vinculo via queryset.update(),
    # entao a instancia em memoria de `enviada` precisa ser recarregada.
    enviada.refresh_from_db()

    return enviada, recebida
