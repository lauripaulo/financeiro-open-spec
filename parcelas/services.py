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

    for indice_calendario, indice_parcela in enumerate(range(parcelas_pagas, total_parcelas), start=1):
        ano, mes = _mes_seguinte(data_compra, indice_calendario)
        valor = valor_parcela if indice_parcela < (total_parcelas - 1) else valor_ultima_parcela
        Lancamento.objects.create(
            descricao=f"{descricao} {indice_parcela + 1}/{total_parcelas}",
            tipo=Lancamento.Tipo.PARCELA_CARTAO,
            data_vencimento=_data_vencimento_segura(ano, mes, conta.dia_vencimento),
            valor=valor,
            conta=conta,
            competencia_ano=ano,
            competencia_mes=mes,
            total_parcelas=total_parcelas,
            parcela_atual=indice_parcela + 1,
            gerado_automaticamente=True,
        )

    return compra


def criar_parcela_importada(*, compra, parcela_atual, valor, competencia_ano, competencia_mes):
    return Lancamento.objects.create(
        descricao=f"{compra.descricao} {parcela_atual}/{compra.total_parcelas}",
        tipo=Lancamento.Tipo.PARCELA_CARTAO,
        data_vencimento=_data_vencimento_segura(
            competencia_ano, competencia_mes, compra.conta.dia_vencimento
        ),
        valor=valor,
        conta=compra.conta,
        competencia_ano=competencia_ano,
        competencia_mes=competencia_mes,
        total_parcelas=compra.total_parcelas,
        parcela_atual=parcela_atual,
        gerado_automaticamente=True,
    )


@transaction.atomic
def registrar_compra_importada(
    *, descricao, valor_parcela, parcela_atual, total_parcelas, conta, data_lancamento, fitid
):
    """Registra uma compra parcelada vinda de importacao OFX.

    O OFX so informa o valor da parcela do mes, nunca o total real da compra;
    o valor_total gravado e uma estimativa (valor_parcela * total_parcelas) e
    as parcelas futuras nascem como projecao com o mesmo valor da parcela
    atual, corrigiveis por importacoes seguintes.
    """
    parcela_atual = int(parcela_atual)
    total_parcelas = int(total_parcelas)

    if not 1 <= parcela_atual <= total_parcelas:
        raise ValidationError({"parcela_atual": "Parcela atual fora do intervalo da compra."})

    valor_parcela = Decimal(valor_parcela)
    compra = CompraParcelada.objects.create(
        descricao=descricao,
        valor_total=(valor_parcela * total_parcelas).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        total_parcelas=total_parcelas,
        conta=conta,
        data_compra=data_lancamento,
        fitid=fitid,
    )

    parcelas = []
    for indice in range(parcela_atual, total_parcelas + 1):
        ano, mes = _mes_seguinte(data_lancamento, indice - parcela_atual)
        parcelas.append(
            criar_parcela_importada(
                compra=compra,
                parcela_atual=indice,
                valor=valor_parcela,
                competencia_ano=ano,
                competencia_mes=mes,
            )
        )

    return compra, parcelas
