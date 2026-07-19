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

MEMO_PAGAMENTO_FATURA = "Pagamento recebido"

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


@transaction.atomic
def importar_ofx_nubank_cartao(*, conta, texto, modo):
    if modo not in (MODO_NOVOS, MODO_SOBRESCREVER):
        raise ValidationError(f"Modo de importacao invalido: {modo}")

    acctid, transacoes = parse_ofx_nubank(texto)

    criados, atualizados, pulados = [], [], []
    meses_fechados = set()

    for trn in transacoes:
        if trn.memo == MEMO_PAGAMENTO_FATURA and trn.trntype == "CREDIT":
            pulados.append(
                _item_resumo(trn.memo, trn.valor, trn.data.year, trn.data.month, "pagamento de fatura")
            )
            continue

        parcela = _RE_PARCELA.match(trn.memo)
        if parcela and int(parcela.group("total")) < 2:
            parcela = None

        if parcela:
            chave = chave_dedup_parcela(conta.id, trn.fitid, int(parcela.group("atual")))
        else:
            chave = chave_dedup_simples(conta.id, trn.fitid, trn.memo)

        item = ItemImportado.objects.filter(chave_dedup=chave).select_related("lancamento").first()
        if item is not None:
            _tratar_existente(item, trn, modo, conta, atualizados, pulados)
            continue

        if parcela:
            _criar_parcelada(conta, trn, parcela, chave, acctid, criados)
        else:
            if not MesAberto.objects.filter(ano=trn.data.year, mes=trn.data.month).exists():
                meses_fechados.add((trn.data.year, trn.data.month))
                continue
            _criar_simples(conta, trn, chave, acctid, criados)

    if meses_fechados:
        meses = ", ".join(f"{m:02d}/{a}" for a, m in sorted(meses_fechados))
        raise ValidationError(
            f"Importacao cancelada: ha transacoes em mes nao aberto ({meses}). "
            "Abra o mes antes de importar. Nada foi gravado."
        )

    return {"acctid": acctid, "criados": criados, "atualizados": atualizados, "pulados": pulados}


def _tratar_existente(item, trn, modo, conta, atualizados, pulados):
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

    novo_vencimento = _data_vencimento_segura(ano, mes, conta.dia_vencimento)
    sem_mudanca = (
        lancamento.valor == valor_abs
        and lancamento.competencia_ano == ano
        and lancamento.competencia_mes == mes
        and lancamento.data_vencimento == novo_vencimento
    )
    if sem_mudanca:
        pulados.append(_item_resumo(trn.memo, valor_abs, ano, mes, "sem alteracao"))
        return

    lancamento.valor = valor_abs
    lancamento.competencia_ano = ano
    lancamento.competencia_mes = mes
    lancamento.data_vencimento = novo_vencimento
    lancamento.save()
    atualizados.append(_item_resumo(lancamento.descricao, valor_abs, ano, mes, "projecao corrigida"))


def _criar_parcelada(conta, trn, parcela, chave, acctid, criados):
    descricao = parcela.group("descricao")
    atual = int(parcela.group("atual"))
    total = int(parcela.group("total"))
    valor_abs = abs(trn.valor)

    compra = CompraParcelada.objects.filter(fitid=trn.fitid).first()
    if compra is not None:
        # Compra ja conhecida, mas esta parcela ainda nao (ex.: total de
        # parcelas divergente entre faturas). Cria apenas a parcela que falta.
        lancamento = criar_parcela_importada(
            compra=compra,
            parcela_atual=atual,
            valor=valor_abs,
            competencia_ano=trn.data.year,
            competencia_mes=trn.data.month,
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

    compra, lancamentos = registrar_compra_importada(
        descricao=descricao,
        valor_parcela=valor_abs,
        parcela_atual=atual,
        total_parcelas=total,
        conta=conta,
        data_lancamento=trn.data,
        fitid=trn.fitid,
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


def _criar_simples(conta, trn, chave, acctid, criados):
    valor_abs = abs(trn.valor)
    ano, mes = trn.data.year, trn.data.month
    tipo = (
        Lancamento.Tipo.RECEBIMENTO_EXCEPCIONAL
        if trn.trntype == "CREDIT"
        else Lancamento.Tipo.GASTO_VARIAVEL
    )
    lancamento = Lancamento.objects.create(
        descricao=trn.memo,
        tipo=tipo,
        data_vencimento=_data_vencimento_segura(ano, mes, conta.dia_vencimento),
        valor=valor_abs,
        conta=conta,
        competencia_ano=ano,
        competencia_mes=mes,
        gerado_automaticamente=True,
    )
    ItemImportado.objects.create(
        conta=conta,
        fitid=trn.fitid,
        chave_dedup=chave,
        lancamento=lancamento,
        acctid=acctid,
    )
    criados.append(_item_resumo(trn.memo, valor_abs, ano, mes))
