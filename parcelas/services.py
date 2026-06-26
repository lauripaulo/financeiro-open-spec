from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import calendar

from django.core.exceptions import ValidationError
from django.db import transaction

from lancamentos.models import Lancamento
from parcelas.models import CompraParcelada


def _mes_seguinte(data_base: date, incremento: int):
    mes_base = data_base.month + incremento
    ano = data_base.year + (mes_base - 1) // 12
    mes = ((mes_base - 1) % 12) + 1
    return ano, mes


def _data_vencimento_segura(ano, mes, dia):
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(dia, ultimo_dia))


@transaction.atomic
def gerar_parcelas_da_compra(*, descricao, valor_total, total_parcelas, conta, data_compra, parcelas_pagas=0):
    total_parcelas = int(total_parcelas)
    parcelas_pagas = int(parcelas_pagas)

    if parcelas_pagas < 0:
        raise ValidationError({"parcelas_pagas": "Parcelas pagas nao pode ser negativo."})

    if parcelas_pagas > total_parcelas:
        raise ValidationError({"parcelas_pagas": "Parcelas pagas nao pode ser maior que o total de parcelas."})

    if parcelas_pagas == total_parcelas:
        raise ValidationError({"parcelas_pagas": "Nao ha parcelas a gerar para esta compra."})

    compra = CompraParcelada.objects.create(
        descricao=descricao,
        valor_total=valor_total,
        total_parcelas=total_parcelas,
        conta=conta,
        data_compra=data_compra,
    )

    valor_total = Decimal(valor_total)
    valor_parcela = (valor_total / Decimal(total_parcelas)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    valor_ultima_parcela = (valor_total - (valor_parcela * (total_parcelas - 1))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    for indice in range(parcelas_pagas, total_parcelas):
        ano, mes = _mes_seguinte(data_compra, indice + 1)
        valor = valor_parcela if indice < (total_parcelas - 1) else valor_ultima_parcela
        Lancamento.objects.create(
            descricao=f"{descricao} {indice + 1}/{total_parcelas}",
            tipo=Lancamento.Tipo.PARCELA_CARTAO,
            data_vencimento=_data_vencimento_segura(ano, mes, conta.dia_vencimento),
            valor=valor,
            conta=conta,
            competencia_ano=ano,
            competencia_mes=mes,
            total_parcelas=total_parcelas,
            parcela_atual=indice + 1,
            gerado_automaticamente=True,
        )

    return compra
