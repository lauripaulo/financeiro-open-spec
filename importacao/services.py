import hashlib
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from importacao.models import ItemImportado
from lancamentos.models import Lancamento
from meses.models import MesAberto
from parcelas.models import CompraParcelada
from parcelas.services import (
    _data_vencimento_segura,
    criar_parcela_importada,
    registrar_compra_importada,
)

MODO_NOVOS = "NOVOS"
MODO_SOBRESCREVER = "SOBRESCREVER"

# Prefixos normalizados (strip + lower): sufixos novos do banco nao podem
# desativar o pulo silenciosamente — importar a quitacao da fatura duplicaria
# os gastos do cartao.
MEMO_PAGAMENTO_FATURA_CARTAO = "pagamento recebido"
MEMO_PAGAMENTO_FATURA_CONTA = "pagamento de fatura"

SECAO_CARTAO = "CARTAO"
SECAO_CONTA = "CONTA"

_RE_STMTTRN = re.compile(r"<STMTTRN>(.*?)</STMTTRN>", re.DOTALL | re.IGNORECASE)
_RE_PARCELA = re.compile(r"^(?P<descricao>.+?) - Parcela (?P<atual>\d+)/(?P<total>\d+)$")


@dataclass
class TransacaoOFX:
    trntype: str
    data: date
    valor: Decimal
    fitid: str
    memo: str


def _campo(bloco, tag):
    match = re.search(rf"<{tag}>([^<\r\n]*)", bloco, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def parse_ofx_nubank(texto):
    """Extrai ACCTID e transacoes de um extrato OFX v1 (SGML) do Nubank."""
    if "<OFX>" not in texto.upper():
        raise ValidationError("Arquivo nao parece ser um OFX valido (tag <OFX> ausente).")

    acctid = _campo(texto, "ACCTID")
    transacoes = []
    for bloco in _RE_STMTTRN.findall(texto):
        dtposted = _campo(bloco, "DTPOSTED")
        trnamt = _campo(bloco, "TRNAMT")
        fitid = _campo(bloco, "FITID")
        if len(dtposted) < 8 or not trnamt or not fitid:
            raise ValidationError("Transacao OFX sem DTPOSTED, TRNAMT ou FITID.")
        try:
            data = date(int(dtposted[0:4]), int(dtposted[4:6]), int(dtposted[6:8]))
            valor = Decimal(trnamt)
        except (ValueError, InvalidOperation) as exc:
            raise ValidationError(f"Transacao OFX com data ou valor invalido: {exc}")

        transacoes.append(
            TransacaoOFX(
                trntype=_campo(bloco, "TRNTYPE").upper(),
                data=data,
                valor=valor,
                fitid=fitid,
                memo=_campo(bloco, "MEMO"),
            )
        )

    if not transacoes:
        raise ValidationError("Nenhuma transacao encontrada no arquivo OFX.")

    return acctid, transacoes


def detectar_secao_ofx(texto):
    maiusculo = texto.upper()
    if "<CCSTMTRS>" in maiusculo:
        return SECAO_CARTAO
    if "<STMTRS>" in maiusculo:
        return SECAO_CONTA
    return None


def chave_dedup_parcela(conta_id, fitid, parcela_atual):
    return _sha256(conta_id, fitid, parcela_atual)


def chave_dedup_simples(conta_id, fitid, memo):
    return _sha256(conta_id, fitid, memo)


def _sha256(*partes):
    return hashlib.sha256("|".join(str(p) for p in partes).encode("utf-8")).hexdigest()


def _item_resumo(descricao, valor, ano, mes, motivo=""):
    return {
        "descricao": descricao,
        "valor": str(valor),
        "competencia": f"{mes:02d}/{ano}",
        "motivo": motivo,
    }


def _validar_modo(modo):
    if modo not in (MODO_NOVOS, MODO_SOBRESCREVER):
        raise ValidationError(f"Modo de importacao invalido: {modo}")


def _validar_secao(texto, secao_proibida, mensagem):
    if detectar_secao_ofx(texto) == secao_proibida:
        raise ValidationError(mensagem)


def _validar_acctid(conta, acctid):
    if not acctid:
        return
    divergente = (
        ItemImportado.objects.filter(conta=conta)
        .exclude(acctid="")
        .exclude(acctid=acctid)
        .exists()
    )
    if divergente:
        raise ValidationError(
            "O ACCTID deste arquivo nao confere com importacoes anteriores desta "
            "conta. Confira se o arquivo pertence mesmo a ela. Nada foi gravado."
        )


def _validar_meses_abertos(meses_fechados):
    if meses_fechados:
        meses = ", ".join(f"{m:02d}/{a}" for a, m in sorted(meses_fechados))
        raise ValidationError(
            f"Importacao cancelada: ha transacoes em mes nao aberto ({meses}). "
            "Abra o mes antes de importar. Nada foi gravado."
        )


def _meses_abertos():
    return set(MesAberto.objects.values_list("ano", "mes"))


def _memo_normalizado(trn):
    return trn.memo.strip().lower()


def _e_pagamento_fatura_cartao(trn):
    return _memo_normalizado(trn).startswith(MEMO_PAGAMENTO_FATURA_CARTAO) and trn.valor > 0


def _e_pagamento_fatura_conta(trn):
    return _memo_normalizado(trn).startswith(MEMO_PAGAMENTO_FATURA_CONTA) and trn.valor < 0


DESCRICAO_MAX = 180


def resumir_memo(memo):
    """Reduz memo longo do extrato a "operacao - contraparte".

    Memos da conta Nubank seguem "operacao - contraparte - documento - banco...";
    documento e dados bancarios ficam so em detalhes. Retorna (descricao, detalhes);
    detalhes vazio quando nada foi cortado.
    """
    partes = [parte.strip() for parte in memo.split(" - ")]
    if len(partes) >= 3:
        descricao = " - ".join(partes[:2])
    else:
        descricao = memo

    if len(descricao) > DESCRICAO_MAX:
        descricao = descricao[: DESCRICAO_MAX - 1] + "…"

    detalhes = memo if descricao != memo else ""
    return descricao, detalhes


def _tipo_simples(trn):
    # Sinal de TRNAMT e o campo autoritativo do OFX; TRNTYPE fora de
    # DEBIT/CREDIT (XFER, DEP, PAYMENT...) nao pode virar gasto por engano.
    if trn.valor > 0:
        return Lancamento.Tipo.RECEBIMENTO_EXCEPCIONAL
    return Lancamento.Tipo.GASTO_VARIAVEL


def _buscar_existentes(chaves):
    itens = ItemImportado.objects.filter(chave_dedup__in=chaves).select_related("lancamento")
    return {item.chave_dedup: item for item in itens}


def _com_contexto(trn, funcao):
    try:
        return funcao()
    except ValidationError as exc:
        raise ValidationError(
            f"Erro ao importar '{trn.memo}' ({trn.data.strftime('%d/%m/%Y')}): "
            + " ".join(exc.messages)
        )


def _criar_simples(conta, trn, chave, acctid, criados, *, data_vencimento, data_pagamento=None):
    descricao, detalhes = resumir_memo(trn.memo)
    lancamento = _com_contexto(
        trn,
        lambda: Lancamento.objects.create(
            descricao=descricao,
            detalhes=detalhes,
            tipo=_tipo_simples(trn),
            data_vencimento=data_vencimento,
            data_pagamento=data_pagamento,
            valor=abs(trn.valor),
            conta=conta,
            competencia_ano=trn.data.year,
            competencia_mes=trn.data.month,
            gerado_automaticamente=True,
        ),
    )
    ItemImportado.objects.create(
        conta=conta,
        fitid=trn.fitid,
        chave_dedup=chave,
        lancamento=lancamento,
        acctid=acctid,
    )
    criados.append(_item_resumo(descricao, abs(trn.valor), trn.data.year, trn.data.month))


def _tratar_existente(
    item,
    trn,
    modo,
    atualizados,
    pulados,
    meses_fechados,
    abertos,
    *,
    novo_vencimento,
    novo_pagamento,
    motivo_atualizacao,
):
    lancamento = item.lancamento
    ano, mes = trn.data.year, trn.data.month
    valor_abs = abs(trn.valor)

    if modo == MODO_NOVOS:
        pulados.append(_item_resumo(trn.memo, valor_abs, ano, mes, "ja importado"))
        return

    if lancamento is None:
        pulados.append(_item_resumo(trn.memo, valor_abs, ano, mes, "lancamento original excluido"))
        return

    if lancamento.data_pagamento is not None:
        pulados.append(_item_resumo(trn.memo, valor_abs, ano, mes, "ja pago"))
        return

    alvo_pagamento = lancamento.data_pagamento if novo_pagamento is None else novo_pagamento
    sem_mudanca = (
        lancamento.valor == valor_abs
        and lancamento.competencia_ano == ano
        and lancamento.competencia_mes == mes
        and lancamento.data_vencimento == novo_vencimento
        and lancamento.data_pagamento == alvo_pagamento
    )
    if sem_mudanca:
        pulados.append(_item_resumo(trn.memo, valor_abs, ano, mes, "sem alteracao"))
        return

    # Parcela futura pode viver em mes ainda nao aberto; qualquer outro
    # lancamento nao pode ser movido para competencia fechada.
    if lancamento.tipo != Lancamento.Tipo.PARCELA_CARTAO and (ano, mes) not in abertos:
        meses_fechados.add((ano, mes))
        return

    lancamento.valor = valor_abs
    lancamento.competencia_ano = ano
    lancamento.competencia_mes = mes
    lancamento.data_vencimento = novo_vencimento
    if novo_pagamento is not None:
        lancamento.data_pagamento = novo_pagamento
    _com_contexto(trn, lancamento.save)
    atualizados.append(_item_resumo(lancamento.descricao, valor_abs, ano, mes, motivo_atualizacao))


@transaction.atomic
def importar_ofx_nubank_cartao(*, conta, texto, modo):
    _validar_modo(modo)
    _validar_secao(
        texto,
        SECAO_CONTA,
        "Este arquivo parece ser extrato de conta corrente, nao fatura de cartao. "
        "Use a importacao de OFX da conta Nubank. Nada foi gravado.",
    )
    acctid, transacoes = parse_ofx_nubank(texto)
    _validar_acctid(conta, acctid)

    criados, atualizados, pulados = [], [], []
    meses_fechados = set()
    abertos = _meses_abertos()

    # Passo 1: classifica tudo em memoria e valida meses antes de gravar.
    linhas = []
    for trn in transacoes:
        if _e_pagamento_fatura_cartao(trn):
            pulados.append(
                _item_resumo(trn.memo, trn.valor, trn.data.year, trn.data.month, "pagamento de fatura")
            )
            continue
        if trn.valor == 0:
            pulados.append(
                _item_resumo(trn.memo, trn.valor, trn.data.year, trn.data.month, "valor zero")
            )
            continue

        parcela = _RE_PARCELA.match(trn.memo)
        if parcela and int(parcela.group("total")) < 2:
            parcela = None

        if parcela:
            chave = chave_dedup_parcela(conta.id, trn.fitid, int(parcela.group("atual")))
        else:
            chave = chave_dedup_simples(conta.id, trn.fitid, trn.memo)
        linhas.append((trn, parcela, chave))

    existentes = _buscar_existentes([chave for _, _, chave in linhas])
    for trn, parcela, chave in linhas:
        if chave not in existentes and parcela is None:
            competencia = (trn.data.year, trn.data.month)
            if competencia not in abertos:
                meses_fechados.add(competencia)
    _validar_meses_abertos(meses_fechados)

    # Passo 2: grava.
    chaves_processadas = set()
    for trn, parcela, chave in linhas:
        ano, mes = trn.data.year, trn.data.month
        if chave in chaves_processadas:
            pulados.append(_item_resumo(trn.memo, abs(trn.valor), ano, mes, "duplicado no arquivo"))
            continue
        chaves_processadas.add(chave)

        item = existentes.get(chave)
        if item is not None:
            _tratar_existente(
                item,
                trn,
                modo,
                atualizados,
                pulados,
                meses_fechados,
                abertos,
                novo_vencimento=_data_vencimento_segura(ano, mes, conta.dia_vencimento),
                novo_pagamento=None,
                motivo_atualizacao="projecao corrigida",
            )
            continue

        if parcela:
            _criar_parcelada(conta, trn, parcela, chave, acctid, criados)
        else:
            _criar_simples(
                conta,
                trn,
                chave,
                acctid,
                criados,
                data_vencimento=_data_vencimento_segura(ano, mes, conta.dia_vencimento),
            )

    _validar_meses_abertos(meses_fechados)

    return {"acctid": acctid, "criados": criados, "atualizados": atualizados, "pulados": pulados}


@transaction.atomic
def importar_ofx_nubank_conta(*, conta, texto, modo):
    """Importa extrato OFX da conta corrente Nubank.

    Extrato e fato consumado: todo lancamento nasce pago (data_pagamento =
    data_vencimento = DTPOSTED). Nao ha parcelas em conta corrente.
    """
    _validar_modo(modo)
    _validar_secao(
        texto,
        SECAO_CARTAO,
        "Este arquivo parece ser fatura de cartao, nao extrato de conta corrente. "
        "Use a importacao de OFX do cartao Nubank. Nada foi gravado.",
    )
    acctid, transacoes = parse_ofx_nubank(texto)
    _validar_acctid(conta, acctid)

    criados, atualizados, pulados = [], [], []
    meses_fechados = set()
    abertos = _meses_abertos()

    # Passo 1: classifica tudo em memoria e valida meses antes de gravar.
    linhas = []
    for trn in transacoes:
        if _e_pagamento_fatura_conta(trn):
            pulados.append(
                _item_resumo(trn.memo, abs(trn.valor), trn.data.year, trn.data.month, "pagamento de fatura")
            )
            continue
        if trn.valor == 0:
            pulados.append(
                _item_resumo(trn.memo, trn.valor, trn.data.year, trn.data.month, "valor zero")
            )
            continue
        linhas.append((trn, chave_dedup_simples(conta.id, trn.fitid, trn.memo)))

    existentes = _buscar_existentes([chave for _, chave in linhas])
    for trn, chave in linhas:
        if chave not in existentes:
            competencia = (trn.data.year, trn.data.month)
            if competencia not in abertos:
                meses_fechados.add(competencia)
    _validar_meses_abertos(meses_fechados)

    # Passo 2: grava.
    chaves_processadas = set()
    for trn, chave in linhas:
        if chave in chaves_processadas:
            pulados.append(
                _item_resumo(trn.memo, abs(trn.valor), trn.data.year, trn.data.month, "duplicado no arquivo")
            )
            continue
        chaves_processadas.add(chave)

        item = existentes.get(chave)
        if item is not None:
            _tratar_existente(
                item,
                trn,
                modo,
                atualizados,
                pulados,
                meses_fechados,
                abertos,
                novo_vencimento=trn.data,
                novo_pagamento=trn.data,
                motivo_atualizacao="corrigido pelo extrato",
            )
            continue

        _criar_simples(
            conta,
            trn,
            chave,
            acctid,
            criados,
            data_vencimento=trn.data,
            data_pagamento=trn.data,
        )

    _validar_meses_abertos(meses_fechados)

    return {"acctid": acctid, "criados": criados, "atualizados": atualizados, "pulados": pulados}


def _criar_parcelada(conta, trn, parcela, chave, acctid, criados):
    descricao = parcela.group("descricao")
    atual = int(parcela.group("atual"))
    total = int(parcela.group("total"))
    valor_abs = abs(trn.valor)

    compra = CompraParcelada.objects.filter(conta=conta, fitid=trn.fitid).first()
    if compra is not None:
        # Compra ja conhecida, mas esta parcela ainda nao (ex.: total de
        # parcelas divergente entre faturas). Cria apenas a parcela que falta.
        lancamento = _com_contexto(
            trn,
            lambda: criar_parcela_importada(
                compra=compra,
                parcela_atual=atual,
                valor=valor_abs,
                competencia_ano=trn.data.year,
                competencia_mes=trn.data.month,
            ),
        )
        ItemImportado.objects.create(
            conta=conta,
            fitid=trn.fitid,
            chave_dedup=chave,
            lancamento=lancamento,
            compra=compra,
            acctid=acctid,
        )
        criados.append(
            _item_resumo(lancamento.descricao, valor_abs, trn.data.year, trn.data.month)
        )
        return

    compra, lancamentos = _com_contexto(
        trn,
        lambda: registrar_compra_importada(
            descricao=descricao,
            valor_parcela=valor_abs,
            parcela_atual=atual,
            total_parcelas=total,
            conta=conta,
            data_lancamento=trn.data,
            fitid=trn.fitid,
        ),
    )
    for lancamento in lancamentos:
        ItemImportado.objects.create(
            conta=conta,
            fitid=trn.fitid,
            chave_dedup=chave_dedup_parcela(conta.id, trn.fitid, lancamento.parcela_atual),
            lancamento=lancamento,
            compra=compra,
            acctid=acctid,
        )
        motivo = "" if lancamento.parcela_atual == atual else "projecao de parcela futura"
        criados.append(
            _item_resumo(
                lancamento.descricao,
                lancamento.valor,
                lancamento.competencia_ano,
                lancamento.competencia_mes,
                motivo,
            )
        )
