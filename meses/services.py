from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import calendar

from django.core.exceptions import ValidationError
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


def avisar_limite_meses_futuros(ano, mes):
    hoje = date.today()
    diferenca = (ano - hoje.year) * 12 + (mes - hoje.month)
    return diferenca > 12


def mes_permitido_para_abertura():
    """Retorna (ano, mes) do proximo mes permitido para abertura.

    Se nao ha mes aberto: retorna o mes atual.
    Se ha meses abertos: retorna o mes imediatamente seguinte ao ultimo.
    """
    from django.utils import timezone

    hoje = timezone.localdate()
    ultimo = MesAberto.objects.order_by("-ano", "-mes").first()
    if ultimo is None:
        return hoje.year, hoje.month
    return _mes_posterior(ultimo.ano, ultimo.mes)


def _validar_sequencia_mes(ano, mes):
    """Valida que o mes solicitado segue a sequencia obrigatoria.

    - Se nao ha nenhum mes aberto: apenas o mes atual e permitido.
    - Se ja ha meses abertos: apenas o mes imediatamente seguinte ao ultimo mes aberto e permitido.

    Levanta ValidationError com o mes permitido se a regra for violada.
    Retorna sem erro se o mes ja estiver aberto (idempotente) ou se for valido.
    """
    if MesAberto.objects.filter(ano=ano, mes=mes).exists():
        return  # idempotente: mes ja aberto, nada a fazer

    from django.utils import timezone

    hoje = timezone.localdate()
    ultimo = MesAberto.objects.order_by("-ano", "-mes").first()
    if ultimo is None:
        # Nenhum mes aberto: apenas o mes atual e permitido
        if (ano, mes) != (hoje.year, hoje.month):
            permitido = f"{hoje.month:02d}/{hoje.year}"
            raise ValidationError(
                f"O primeiro mes a ser aberto deve ser o mes atual ({permitido})."
            )
    else:
        # Ja ha meses abertos: apenas o imediatamente seguinte e permitido
        ano_permitido, mes_permitido = _mes_posterior(ultimo.ano, ultimo.mes)
        if (ano, mes) != (ano_permitido, mes_permitido):
            permitido = f"{mes_permitido:02d}/{ano_permitido}"
            raise ValidationError(
                f"Apenas o mes imediatamente seguinte pode ser aberto. Mes permitido: {permitido}."
            )


@transaction.atomic
def criar_mes(ano, mes):
    _validar_sequencia_mes(ano, mes)

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
            saldo_inicial = saldo_do_mes(conta, ano_anterior, mes_anterior)
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
        ).pendentes()

        for origem in Lancamento.objects.filter(competencia_ano=ano_anterior, competencia_mes=mes_anterior):
            if origem.tipo not in Lancamento.TIPOS_PROPAGAVEIS:
                continue

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


def elegivel_para_transferencia(lancamento, ano_destino, mes_destino):
    ano_anterior, mes_anterior = _mes_anterior(ano_destino, mes_destino)
    if (lancamento.competencia_ano, lancamento.competencia_mes) != (ano_anterior, mes_anterior):
        return False
    return lancamento.status == Lancamento.Status.PENDENTE


@transaction.atomic
def transferir_pendente_para_mes(lancamento, ano_destino, mes_destino):
    if not elegivel_para_transferencia(lancamento, ano_destino, mes_destino):
        raise ValidationError(
            "Apenas lancamentos pendentes do mes imediatamente anterior podem ser transferidos."
        )
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


@dataclass(frozen=True)
class SaldoConta:
    inicial: Decimal
    final: Decimal


def saldos_do_mes(contas, ano, mes, status_incluidos=None):
    """Regra de saldo mensal por conta — implementacao unica do sistema.

    Saldo inicial registrado em SaldoMensalConta (fallback em
    conta.saldo_atual) + entradas - saidas do mes. Versao batch: numero
    de consultas independe do numero de contas (uma de SaldoMensalConta,
    uma de Lancamento). Retorna {conta_id: SaldoConta(inicial, final)}.
    """
    contas = list(contas)
    registrados = dict(
        SaldoMensalConta.objects.filter(conta__in=contas, ano=ano, mes=mes).values_list(
            "conta_id", "saldo_inicial"
        )
    )

    lancamentos = Lancamento.objects.filter(
        conta__in=contas, competencia_ano=ano, competencia_mes=mes
    )
    if status_incluidos:
        lancamentos = lancamentos.com_status_in(status_incluidos)

    movimentos = {conta.pk: Decimal("0.00") for conta in contas}
    for lancamento in lancamentos:
        if lancamento.direcao == "ENTRADA":
            movimentos[lancamento.conta_id] += lancamento.valor_absoluto
        else:
            movimentos[lancamento.conta_id] -= lancamento.valor_absoluto

    saldos = {}
    for conta in contas:
        inicial = registrados.get(conta.pk)
        if inicial is None:
            inicial = conta.saldo_atual or Decimal("0.00")
        saldos[conta.pk] = SaldoConta(inicial=inicial, final=inicial + movimentos[conta.pk])
    return saldos


def saldo_do_mes(conta, ano, mes, status_incluidos=None):
    return saldos_do_mes([conta], ano, mes, status_incluidos=status_incluidos)[conta.pk].final


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
    ).pendentes()


def mes_anterior_posterior(ano, mes):
    return _mes_anterior(ano, mes), _mes_posterior(ano, mes)


def _saldo_inicial_do_mes(conta: Conta, ano: int, mes: int) -> Decimal:
    """Retorna o saldo inicial registrado em SaldoMensalConta para o mes,
    com fallback para conta.saldo_atual se o registro nao existir."""
    try:
        smc = SaldoMensalConta.objects.get(conta=conta, ano=ano, mes=mes)
        return smc.saldo_inicial
    except SaldoMensalConta.DoesNotExist:
        return conta.saldo_atual or Decimal("0.00")


def _soma_movimentos(lancamentos) -> Decimal:
    """Soma entradas e subtrai saidas para uma queryset de lancamentos."""
    total = Decimal("0.00")
    for lancamento in lancamentos:
        if lancamento.direcao == "ENTRADA":
            total += lancamento.valor_absoluto
        else:
            total -= lancamento.valor_absoluto
    return total


def _mes_referencia_seguro(data: date) -> tuple[int, int]:
    """Retorna (ano, mes) da data se o mes estiver aberto,
    senao retorna (ano, mes) do ultimo mes aberto."""
    if MesAberto.objects.filter(ano=data.year, mes=data.month).exists():
        return data.year, data.month
    ultimo = MesAberto.objects.order_by("-ano", "-mes").first()
    if ultimo is None:
        return data.year, data.month
    return ultimo.ano, ultimo.mes


def saldo_real_em_data(conta: Conta, data: date) -> Decimal:
    """Saldo real da conta na data especificada.

    Ancora: SaldoMensalConta do mes da data (fallback conta.saldo_atual).
    Soma apenas lancamentos PAGOS (data_pagamento IS NOT NULL e <= data)
    restritos ao competencia_mes da data de referencia.
    """
    ano, mes = _mes_referencia_seguro(data)
    inicial = _saldo_inicial_do_mes(conta, ano, mes)

    pagos = Lancamento.objects.filter(
        conta=conta,
        competencia_ano=ano,
        competencia_mes=mes,
        data_pagamento__isnull=False,
        data_pagamento__lte=data,
    )
    return inicial + _soma_movimentos(pagos)


def saldo_projetado_em_data(conta: Conta, data: date) -> Decimal:
    """Saldo projetado da conta na data especificada.

    Ancora: mesma que saldo_real_em_data.
    Soma lancamentos PAGOS ate data OU lancamentos com
    data_vencimento <= data (pagos ou nao), restritos ao
    competencia_mes da data de referencia.
    """
    ano, mes = _mes_referencia_seguro(data)
    inicial = _saldo_inicial_do_mes(conta, ano, mes)

    lancamentos = Lancamento.objects.filter(
        conta=conta,
        competencia_ano=ano,
        competencia_mes=mes,
    ).filter(
        Q(data_pagamento__isnull=False, data_pagamento__lte=data)
        | Q(data_pagamento__isnull=True, data_vencimento__lte=data)
    )
    return inicial + _soma_movimentos(lancamentos)


def total_gastos_cartao_por_mes(contas_cartao):
    """Total de saidas por mes para contas Cartao.

    Retorna {(ano, mes): {conta_id: Decimal}} para o mes atual
    e ate 3 meses futuros abertos (maximo 4 meses).
    Inclui lancamentos de qualquer status (pagos, pendentes ou previstos).
    """
    hoje = date.today()

    meses_abertos = list(
        MesAberto.objects.filter(
            Q(ano__gt=hoje.year)
            | Q(ano=hoje.year, mes__gte=hoje.month)
        )
        .order_by("ano", "mes")
        .values_list("ano", "mes")[:4]
    )

    if not meses_abertos:
        return {}

    contas_list = list(contas_cartao)
    conta_ids = [c.pk for c in contas_list]

    resultado: dict[tuple[int, int], dict[int, Decimal]] = {}
    for ano, mes in meses_abertos:
        resultado[(ano, mes)] = {c.pk: Decimal("0.00") for c in contas_list}

    lancamentos = Lancamento.objects.filter(
        conta_id__in=conta_ids,
    ).filter(
        Q(*[Q(competencia_ano=a, competencia_mes=m) for a, m in meses_abertos], _connector=Q.OR)
    )

    for lancamento in lancamentos:
        chave = (lancamento.competencia_ano, lancamento.competencia_mes)
        if chave in resultado and lancamento.conta_id in resultado[chave]:
            if lancamento.direcao == "SAIDA":
                resultado[chave][lancamento.conta_id] += lancamento.valor_absoluto

    return resultado
