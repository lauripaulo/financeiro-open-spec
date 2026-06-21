from datetime import date
from decimal import Decimal
import calendar

from django.db import transaction
from django.db.models import Q, Sum

from contas.models import Conta
from lancamentos.models import Lancamento
from meses.models import MesAberto, SaldoMensalConta


def _mes_anterior(ano, mes):
    if mes == 1:
        return ano - 1, 12
    return ano, mes - 1


def _mes_posterior(ano, mes):
    if mes == 12:
        return ano + 1, 1
    return ano, mes + 1


def _data_mes_segura(ano, mes, dia):
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(dia, ultimo_dia))


def _saldo_final_periodo(conta, ano, mes):
    saldo = (
        SaldoMensalConta.objects.filter(conta=conta, ano=ano, mes=mes)
        .values_list("saldo_inicial", flat=True)
        .first()
    )
    if saldo is None:
        saldo = conta.saldo_atual or Decimal("0.00")

    lancamentos = Lancamento.objects.filter(conta=conta, competencia_ano=ano, competencia_mes=mes)
    for lancamento in lancamentos:
        if lancamento.direcao == "ENTRADA":
            saldo += lancamento.valor_absoluto
        else:
            saldo -= lancamento.valor_absoluto
    return saldo


def avisar_limite_meses_futuros(ano, mes):
    hoje = date.today()
    diferenca = (ano - hoje.year) * 12 + (mes - hoje.month)
    return diferenca > 12


@transaction.atomic
def criar_mes(ano, mes):
    mes_aberto, criado = MesAberto.objects.get_or_create(ano=ano, mes=mes)
    avisar_limite = avisar_limite_meses_futuros(ano, mes)

    if not criado:
        return mes_aberto, [], Lancamento.objects.none(), avisar_limite

    ano_anterior, mes_anterior = _mes_anterior(ano, mes)
    mes_anterior_existe = MesAberto.objects.filter(ano=ano_anterior, mes=mes_anterior).exists()

    criados = []
    pendentes = Lancamento.objects.none()

    for conta in Conta.objects.all():
        if mes_anterior_existe:
            saldo_inicial = _saldo_final_periodo(conta, ano_anterior, mes_anterior)
        else:
            saldo_inicial = conta.saldo_atual or Decimal("0.00")

        SaldoMensalConta.objects.get_or_create(
            conta=conta,
            ano=ano,
            mes=mes,
            defaults={"saldo_inicial": saldo_inicial},
        )

    if mes_anterior_existe:
        pendentes = Lancamento.objects.filter(
            competencia_ano=ano_anterior,
            competencia_mes=mes_anterior,
            data_pagamento__isnull=True,
            data_vencimento__lt=date.today(),
        )

        for origem in Lancamento.objects.filter(competencia_ano=ano_anterior, competencia_mes=mes_anterior):
            if origem.tipo in {
                Lancamento.Tipo.RECEBIMENTO_EXCEPCIONAL,
                Lancamento.Tipo.GASTO_VARIAVEL,
                Lancamento.Tipo.CONCILIACAO,
                Lancamento.Tipo.APORTE,
                Lancamento.Tipo.RESGATE,
            }:
                continue

            if origem.tipo == Lancamento.Tipo.PARCELA_CARTAO:
                if origem.parcela_atual >= origem.total_parcelas:
                    continue
                parcela_atual = origem.parcela_atual + 1
                vencimento = _data_mes_segura(ano, mes, origem.conta.dia_vencimento)
                descricao = origem.descricao.rsplit(" ", 1)[0] + f" {parcela_atual}/{origem.total_parcelas}"
            else:
                parcela_atual = None
                vencimento = _data_mes_segura(ano, mes, origem.data_vencimento.day)
                descricao = origem.descricao

            novo = Lancamento.objects.create(
                descricao=descricao,
                tipo=origem.tipo,
                data_vencimento=vencimento,
                valor=origem.valor,
                conta=origem.conta,
                competencia_ano=ano,
                competencia_mes=mes,
                grupo_recorrencia=origem.grupo_recorrencia or origem,
                total_parcelas=origem.total_parcelas,
                parcela_atual=parcela_atual,
                gerado_automaticamente=True,
            )
            criados.append(novo)

    return mes_aberto, criados, pendentes, avisar_limite


@transaction.atomic
def atualizar_serie_futura(lancamento, **novos_campos):
    if not lancamento.is_recorrente:
        for campo, valor in novos_campos.items():
            setattr(lancamento, campo, valor)
        lancamento.save()
        return

    raiz = lancamento.grupo_recorrencia or lancamento
    for item in Lancamento.objects.filter(grupo_recorrencia=raiz):
        if (item.competencia_ano, item.competencia_mes) < (lancamento.competencia_ano, lancamento.competencia_mes):
            continue
        for campo, valor in novos_campos.items():
            setattr(item, campo, valor)
        item.save()


@transaction.atomic
def excluir_serie_futura(lancamento):
    if not lancamento.is_recorrente:
        lancamento.delete()
        return

    raiz = lancamento.grupo_recorrencia or lancamento
    Lancamento.objects.filter(
        grupo_recorrencia=raiz,
        competencia_ano__gte=lancamento.competencia_ano,
    ).filter(
        Q(competencia_ano__gt=lancamento.competencia_ano)
        | Q(competencia_ano=lancamento.competencia_ano, competencia_mes__gte=lancamento.competencia_mes)
    ).delete()


@transaction.atomic
def transferir_pendente_para_mes(lancamento, ano_destino, mes_destino):
    lancamento.competencia_ano = ano_destino
    lancamento.competencia_mes = mes_destino
    lancamento.save(update_fields=["competencia_ano", "competencia_mes"])
    return lancamento


@transaction.atomic
def ajustar_saldo_inicial(conta, ano, mes, novo_saldo):
    registro, _ = SaldoMensalConta.objects.get_or_create(
        conta=conta,
        ano=ano,
        mes=mes,
        defaults={"saldo_inicial": novo_saldo},
    )
    diferenca = Decimal(novo_saldo) - registro.saldo_inicial
    if diferenca == Decimal("0.00"):
        return registro, None

    registro.saldo_inicial = novo_saldo
    registro.save(update_fields=["saldo_inicial"])

    conciliacao = Lancamento.objects.create(
        descricao=f"Conciliacao {mes:02d}/{ano}",
        tipo=Lancamento.Tipo.CONCILIACAO,
        data_vencimento=date(ano, mes, 1),
        valor=diferenca,
        conta=conta,
        competencia_ano=ano,
        competencia_mes=mes,
        gerado_automaticamente=True,
    )
    return registro, conciliacao


def saldo_do_mes(conta, ano, mes, status_incluidos=None):
    saldo = (
        SaldoMensalConta.objects.filter(conta=conta, ano=ano, mes=mes)
        .values_list("saldo_inicial", flat=True)
        .first()
    )
    if saldo is None:
        saldo = conta.saldo_atual or Decimal("0.00")

    lancamentos = list(Lancamento.objects.filter(conta=conta, competencia_ano=ano, competencia_mes=mes))
    if status_incluidos:
        status_normalizados = {status.upper() for status in status_incluidos}
        lancamentos = [item for item in lancamentos if item.status in status_normalizados]

    for lancamento in lancamentos:
        if lancamento.direcao == "ENTRADA":
            saldo += lancamento.valor_absoluto
        else:
            saldo -= lancamento.valor_absoluto

    return saldo


def saldo_investimento(conta, ate_ano=None, ate_mes=None):
    if conta.tipo != Conta.Tipo.INVESTIMENTO:
        return Decimal("0.00")

    saldo = conta.saldo_atual or Decimal("0.00")
    qs = Lancamento.objects.filter(conta=conta, tipo__in=[Lancamento.Tipo.APORTE, Lancamento.Tipo.RESGATE])

    if ate_ano is not None and ate_mes is not None:
        qs = qs.filter(Q(competencia_ano__lt=ate_ano) | Q(competencia_ano=ate_ano, competencia_mes__lte=ate_mes))

    aportes = qs.filter(tipo=Lancamento.Tipo.APORTE).aggregate(total=Sum("valor"))["total"] or Decimal("0.00")
    resgates = qs.filter(tipo=Lancamento.Tipo.RESGATE).aggregate(total=Sum("valor"))["total"] or Decimal("0.00")
    return saldo + aportes - resgates


def pendentes_mes_anterior(ano, mes):
    ano_ant, mes_ant = _mes_anterior(ano, mes)
    return Lancamento.objects.filter(
        competencia_ano=ano_ant,
        competencia_mes=mes_ant,
        data_pagamento__isnull=True,
        data_vencimento__lt=date.today(),
    )


def mes_anterior_posterior(ano, mes):
    return _mes_anterior(ano, mes), _mes_posterior(ano, mes)
