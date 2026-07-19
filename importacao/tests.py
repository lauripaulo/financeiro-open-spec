from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from contas.models import Conta
from importacao.models import ItemImportado
from importacao.services import (
    MODO_NOVOS,
    MODO_SOBRESCREVER,
    importar_ofx_nubank_cartao,
    parse_ofx_nubank,
)
from lancamentos.models import Lancamento
from meses.models import MesAberto
from parcelas.models import CompraParcelada


def ofx(*transacoes):
    blocos = "".join(
        f"""
<STMTTRN>
<TRNTYPE>{t.get("trntype", "DEBIT")}</TRNTYPE>
<DTPOSTED>{t["data"]}000000[-3:BRT]</DTPOSTED>
<TRNAMT>{t["valor"]}</TRNAMT>
<FITID>{t["fitid"]}</FITID>
<MEMO>{t["memo"]}</MEMO>
</STMTTRN>"""
        for t in transacoes
    )
    return f"""OFXHEADER:100
DATA:OFXSGML
<OFX>
<CCACCTFROM>
<ACCTID>acct-uuid-nubank</ACCTID>
</CCACCTFROM>
<BANKTRANLIST>{blocos}
</BANKTRANLIST>
</OFX>"""


class ParserOFXTests(TestCase):
    def test_parse_extrai_acctid_e_transacoes(self):
        texto = ofx(
            {"data": "20260719", "valor": "-80.30", "fitid": "f1", "memo": "Fernandalemos"},
            {"data": "20260717", "valor": "4.89", "fitid": "f2", "memo": "IOF de volta", "trntype": "CREDIT"},
        )
        acctid, transacoes = parse_ofx_nubank(texto)

        self.assertEqual(acctid, "acct-uuid-nubank")
        self.assertEqual(len(transacoes), 2)
        self.assertEqual(transacoes[0].data, date(2026, 7, 19))
        self.assertEqual(transacoes[0].valor, Decimal("-80.30"))
        self.assertEqual(transacoes[0].trntype, "DEBIT")
        self.assertEqual(transacoes[1].valor, Decimal("4.89"))

    def test_arquivo_sem_tag_ofx_rejeitado(self):
        with self.assertRaises(ValidationError):
            parse_ofx_nubank("nada a ver")

    def test_arquivo_sem_transacoes_rejeitado(self):
        with self.assertRaises(ValidationError):
            parse_ofx_nubank("<OFX><ACCTID>x</ACCTID></OFX>")


class ImportacaoBase(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(nome="Nubank", tipo=Conta.Tipo.CARTAO, dia_vencimento=8)
        MesAberto.objects.create(ano=2026, mes=7)


class ImportacaoSimplesTests(ImportacaoBase):
    def test_debit_vira_gasto_variavel(self):
        texto = ofx({"data": "20260719", "valor": "-80.30", "fitid": "f1", "memo": "Fernandalemos"})
        resumo = importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        self.assertEqual(len(resumo["criados"]), 1)
        lanc = Lancamento.objects.get()
        self.assertEqual(lanc.tipo, Lancamento.Tipo.GASTO_VARIAVEL)
        self.assertEqual(lanc.valor, Decimal("80.30"))
        self.assertEqual((lanc.competencia_ano, lanc.competencia_mes), (2026, 7))
        self.assertEqual(lanc.data_vencimento, date(2026, 7, 8))
        self.assertTrue(lanc.gerado_automaticamente)
        self.assertIsNone(lanc.data_pagamento)
        item = ItemImportado.objects.get()
        self.assertEqual(item.acctid, "acct-uuid-nubank")

    def test_credit_estorno_vira_recebimento_excepcional(self):
        texto = ofx(
            {"data": "20260717", "valor": "4.89", "fitid": "f2", "memo": "IOF de volta", "trntype": "CREDIT"}
        )
        importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        lanc = Lancamento.objects.get()
        self.assertEqual(lanc.tipo, Lancamento.Tipo.RECEBIMENTO_EXCEPCIONAL)
        self.assertEqual(lanc.valor, Decimal("4.89"))

    def test_pagamento_recebido_pulado(self):
        texto = ofx(
            {"data": "20260704", "valor": "18542.10", "fitid": "f3", "memo": "Pagamento recebido", "trntype": "CREDIT"}
        )
        resumo = importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        self.assertEqual(Lancamento.objects.count(), 0)
        self.assertEqual(resumo["pulados"][0]["motivo"], "pagamento de fatura")

    def test_reimportar_mesmo_arquivo_e_idempotente(self):
        texto = ofx({"data": "20260719", "valor": "-80.30", "fitid": "f1", "memo": "Fernandalemos"})
        importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)
        resumo = importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        self.assertEqual(Lancamento.objects.count(), 1)
        self.assertEqual(len(resumo["criados"]), 0)
        self.assertEqual(resumo["pulados"][0]["motivo"], "ja importado")

    def test_iof_e_compra_com_mesmo_fitid_geram_dois_itens(self):
        texto = ofx(
            {"data": "20260718", "valor": "-4.89", "fitid": "fx", "memo": "IOF de compra internacional"},
            {"data": "20260718", "valor": "-139.73", "fitid": "fx", "memo": "Openrouter, Inc"},
        )
        importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        self.assertEqual(Lancamento.objects.count(), 2)
        self.assertEqual(ItemImportado.objects.count(), 2)

    def test_mes_nao_aberto_cancela_importacao(self):
        texto = ofx(
            {"data": "20260719", "valor": "-80.30", "fitid": "f1", "memo": "Fernandalemos"},
            {"data": "20260619", "valor": "-10.00", "fitid": "f9", "memo": "Mes fechado"},
        )
        with self.assertRaises(ValidationError) as ctx:
            importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        self.assertIn("06/2026", " ".join(ctx.exception.messages))
        self.assertEqual(Lancamento.objects.count(), 0)
        self.assertEqual(ItemImportado.objects.count(), 0)


class ImportacaoParceladaTests(ImportacaoBase):
    def parcela(self, atual, total, valor, fitid="fp1", data="20260714", nome="Idoc3d"):
        return {
            "data": data,
            "valor": valor,
            "fitid": fitid,
            "memo": f"{nome} - Parcela {atual}/{total}",
        }

    def test_cria_compra_e_projeta_parcelas_futuras(self):
        texto = ofx(self.parcela(1, 3, "-296.68"))
        resumo = importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        compra = CompraParcelada.objects.get()
        self.assertEqual(compra.fitid, "fp1")
        self.assertEqual(compra.valor_total, Decimal("890.04"))

        lancamentos = Lancamento.objects.order_by("parcela_atual")
        self.assertEqual(lancamentos.count(), 3)
        self.assertEqual(
            [(l.parcela_atual, l.competencia_mes) for l in lancamentos],
            [(1, 7), (2, 8), (3, 9)],
        )
        for lanc in lancamentos:
            self.assertEqual(lanc.tipo, Lancamento.Tipo.PARCELA_CARTAO)
            self.assertEqual(lanc.valor, Decimal("296.68"))
        self.assertEqual(ItemImportado.objects.count(), 3)
        self.assertEqual(len(resumo["criados"]), 3)

    def test_compra_no_meio_gera_somente_parcelas_restantes(self):
        texto = ofx(self.parcela(4, 12, "-423.25", fitid="fvivo", nome="Vivo Lj"))
        importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        lancamentos = Lancamento.objects.order_by("parcela_atual")
        self.assertEqual(lancamentos.count(), 9)
        self.assertEqual(lancamentos.first().parcela_atual, 4)
        self.assertEqual(lancamentos.last().parcela_atual, 12)

    def test_fatura_seguinte_sobrescreve_projecao(self):
        importar_ofx_nubank_cartao(
            conta=self.conta, texto=ofx(self.parcela(1, 3, "-296.68")), modo=MODO_NOVOS
        )
        texto2 = ofx(self.parcela(2, 3, "-296.66", data="20260814"))
        resumo = importar_ofx_nubank_cartao(conta=self.conta, texto=texto2, modo=MODO_SOBRESCREVER)

        self.assertEqual(Lancamento.objects.count(), 3)
        parcela2 = Lancamento.objects.get(parcela_atual=2)
        self.assertEqual(parcela2.valor, Decimal("296.66"))
        self.assertEqual(parcela2.data_vencimento, date(2026, 8, 8))
        self.assertEqual(len(resumo["atualizados"]), 1)
        self.assertEqual(resumo["atualizados"][0]["motivo"], "projecao corrigida")

    def test_fatura_seguinte_modo_novos_nao_toca_projecao(self):
        importar_ofx_nubank_cartao(
            conta=self.conta, texto=ofx(self.parcela(1, 3, "-296.68")), modo=MODO_NOVOS
        )
        resumo = importar_ofx_nubank_cartao(
            conta=self.conta,
            texto=ofx(self.parcela(2, 3, "-296.66", data="20260814")),
            modo=MODO_NOVOS,
        )

        parcela2 = Lancamento.objects.get(parcela_atual=2)
        self.assertEqual(parcela2.valor, Decimal("296.68"))
        self.assertEqual(resumo["pulados"][0]["motivo"], "ja importado")

    def test_parcela_paga_nunca_sobrescrita(self):
        importar_ofx_nubank_cartao(
            conta=self.conta, texto=ofx(self.parcela(1, 3, "-296.68")), modo=MODO_NOVOS
        )
        parcela2 = Lancamento.objects.get(parcela_atual=2)
        parcela2.data_pagamento = date(2026, 8, 8)
        parcela2.save()

        resumo = importar_ofx_nubank_cartao(
            conta=self.conta,
            texto=ofx(self.parcela(2, 3, "-296.66", data="20260814")),
            modo=MODO_SOBRESCREVER,
        )

        parcela2.refresh_from_db()
        self.assertEqual(parcela2.valor, Decimal("296.68"))
        self.assertEqual(resumo["pulados"][0]["motivo"], "ja pago")

    def test_sobrescrever_sem_mudanca_e_pulado(self):
        texto = ofx(self.parcela(1, 3, "-296.68"))
        importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)
        resumo = importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_SOBRESCREVER)

        self.assertEqual(len(resumo["atualizados"]), 0)
        self.assertEqual(resumo["pulados"][0]["motivo"], "sem alteracao")

    def test_duas_compras_iguais_no_mesmo_dia_fitids_diferentes(self):
        texto = ofx(
            self.parcela(1, 3, "-113.32", fitid="fm1", nome="M6 Confecc"),
            self.parcela(1, 3, "-119.99", fitid="fm2", nome="M6 Confecc"),
        )
        importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        self.assertEqual(CompraParcelada.objects.count(), 2)
        self.assertEqual(Lancamento.objects.count(), 6)


class ImportacaoViewsTests(ImportacaoBase):
    def test_index_lista_opcao_nubank(self):
        resposta = self.client.get(reverse("importacao:index"))
        self.assertContains(resposta, "OFX do cartao Nubank")

    def test_fluxo_upload_completo(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        texto = ofx({"data": "20260719", "valor": "-80.30", "fitid": "f1", "memo": "Fernandalemos"})
        arquivo = SimpleUploadedFile("fatura.ofx", texto.encode("cp1252"))
        resposta = self.client.post(
            reverse("importacao:nubank_cartao"),
            {"arquivo": arquivo, "conta": self.conta.id, "modo": MODO_NOVOS},
            follow=True,
        )

        self.assertContains(resposta, "Resultado da importacao")
        self.assertContains(resposta, "Fernandalemos")
        self.assertEqual(Lancamento.objects.count(), 1)

    def test_erro_de_mes_fechado_aparece_no_form(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        texto = ofx({"data": "20260619", "valor": "-10.00", "fitid": "f9", "memo": "Mes fechado"})
        arquivo = SimpleUploadedFile("fatura.ofx", texto.encode("cp1252"))
        resposta = self.client.post(
            reverse("importacao:nubank_cartao"),
            {"arquivo": arquivo, "conta": self.conta.id, "modo": MODO_NOVOS},
        )

        self.assertContains(resposta, "06/2026")
        self.assertEqual(Lancamento.objects.count(), 0)


class ParserOFXEdgeTests(TestCase):
    def test_transacao_sem_fitid_rejeitada(self):
        texto = """<OFX><ACCTID>a</ACCTID><STMTTRN>
<TRNTYPE>DEBIT</TRNTYPE>
<DTPOSTED>20260719000000[-3:BRT]</DTPOSTED>
<TRNAMT>-10.00</TRNAMT>
<MEMO>Sem fitid</MEMO>
</STMTTRN></OFX>"""
        with self.assertRaises(ValidationError):
            parse_ofx_nubank(texto)

    def test_transacao_sem_valor_rejeitada(self):
        texto = """<OFX><ACCTID>a</ACCTID><STMTTRN>
<TRNTYPE>DEBIT</TRNTYPE>
<DTPOSTED>20260719000000[-3:BRT]</DTPOSTED>
<FITID>f1</FITID>
<MEMO>Sem valor</MEMO>
</STMTTRN></OFX>"""
        with self.assertRaises(ValidationError):
            parse_ofx_nubank(texto)

    def test_data_invalida_rejeitada(self):
        texto = ofx({"data": "20261399", "valor": "-10.00", "fitid": "f1", "memo": "Data ruim"})
        with self.assertRaises(ValidationError):
            parse_ofx_nubank(texto)

    def test_valor_invalido_rejeitado(self):
        texto = ofx({"data": "20260719", "valor": "abc", "fitid": "f1", "memo": "Valor ruim"})
        with self.assertRaises(ValidationError):
            parse_ofx_nubank(texto)

    def test_tags_minusculas_aceitas(self):
        texto = """<ofx><acctid>a-min</acctid><stmttrn>
<trntype>debit</trntype>
<dtposted>20260719000000</dtposted>
<trnamt>-10.00</trnamt>
<fitid>f1</fitid>
<memo>Minusculo</memo>
</stmttrn></ofx>"""
        acctid, transacoes = parse_ofx_nubank(texto)

        self.assertEqual(acctid, "a-min")
        self.assertEqual(transacoes[0].trntype, "DEBIT")
        self.assertEqual(transacoes[0].memo, "Minusculo")


class ImportacaoServicoEdgeTests(ImportacaoBase):
    def test_modo_invalido_rejeitado(self):
        texto = ofx({"data": "20260719", "valor": "-80.30", "fitid": "f1", "memo": "X"})
        with self.assertRaises(ValidationError):
            importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo="QUALQUER")

    def test_memo_parcela_1_de_1_tratado_como_gasto_simples(self):
        texto = ofx({"data": "20260719", "valor": "-50.00", "fitid": "f1", "memo": "Loja - Parcela 1/1"})
        importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        lanc = Lancamento.objects.get()
        self.assertEqual(lanc.tipo, Lancamento.Tipo.GASTO_VARIAVEL)
        self.assertEqual(CompraParcelada.objects.count(), 0)

    def test_lancamento_excluido_nao_e_recriado_no_sobrescrever(self):
        texto = ofx({"data": "20260719", "valor": "-80.30", "fitid": "f1", "memo": "Fernandalemos"})
        importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)
        Lancamento.objects.get().delete()

        resumo = importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_SOBRESCREVER)

        self.assertEqual(Lancamento.objects.count(), 0)
        self.assertEqual(resumo["pulados"][0]["motivo"], "lancamento original excluido")

    def test_pagamento_recebido_como_debit_nao_e_pulado(self):
        texto = ofx({"data": "20260719", "valor": "-10.00", "fitid": "f1", "memo": "Pagamento recebido"})
        resumo = importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        self.assertEqual(len(resumo["criados"]), 1)
        self.assertEqual(Lancamento.objects.count(), 1)

    def test_compra_conhecida_com_parcela_nova_cria_somente_a_faltante(self):
        compra = CompraParcelada.objects.create(
            descricao="Compra Antiga",
            conta=self.conta,
            valor_total=Decimal("300.00"),
            total_parcelas=3,
            data_compra=date(2026, 6, 1),
            fitid="fantigo",
        )
        texto = ofx({"data": "20260719", "valor": "-100.00", "fitid": "fantigo", "memo": "Compra Antiga - Parcela 2/3"})
        resumo = importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        self.assertEqual(CompraParcelada.objects.count(), 1)
        lanc = Lancamento.objects.get()
        self.assertEqual(lanc.parcela_atual, 2)
        self.assertEqual(lanc.descricao, "Compra Antiga 2/3")
        item = ItemImportado.objects.get()
        self.assertEqual(item.compra, compra)
        self.assertEqual(len(resumo["criados"]), 1)


class ItemImportadoModelTests(ImportacaoBase):
    def test_chave_dedup_unica(self):
        from django.db import IntegrityError

        ItemImportado.objects.create(conta=self.conta, fitid="f1", chave_dedup="abc")
        with self.assertRaises(IntegrityError):
            ItemImportado.objects.create(conta=self.conta, fitid="f2", chave_dedup="abc")

    def test_str_contem_fitid_e_conta(self):
        item = ItemImportado.objects.create(conta=self.conta, fitid="f1", chave_dedup="abc")
        self.assertIn("f1", str(item))
        self.assertIn("Nubank", str(item))


class ImportacaoFormTests(ImportacaoBase):
    def post_form(self, texto_bytes, conta_id=None, modo=MODO_NOVOS):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from importacao.forms import ImportacaoOFXNubankCartaoForm

        arquivo = SimpleUploadedFile("fatura.ofx", texto_bytes)
        return ImportacaoOFXNubankCartaoForm(
            {"conta": conta_id or self.conta.id, "modo": modo},
            {"arquivo": arquivo},
        )

    def test_form_valido_decodifica_utf8(self):
        texto = ofx({"data": "20260719", "valor": "-10.00", "fitid": "f1", "memo": "Café São"})
        form = self.post_form(texto.encode("utf-8"))

        self.assertTrue(form.is_valid(), form.errors)
        self.assertIn("Café São", form.cleaned_data["texto"])

    def test_form_valido_decodifica_cp1252(self):
        texto = ofx({"data": "20260719", "valor": "-10.00", "fitid": "f1", "memo": "Café São"})
        form = self.post_form(texto.encode("cp1252"))

        self.assertTrue(form.is_valid(), form.errors)
        self.assertIn("Café São", form.cleaned_data["texto"])

    def test_conta_banco_rejeitada(self):
        banco = Conta.objects.create(nome="Banco X", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("0.00"))
        texto = ofx({"data": "20260719", "valor": "-10.00", "fitid": "f1", "memo": "X"})
        form = self.post_form(texto.encode("utf-8"), conta_id=banco.id)

        self.assertFalse(form.is_valid())
        self.assertIn("conta", form.errors)

    def test_modo_invalido_rejeitado(self):
        texto = ofx({"data": "20260719", "valor": "-10.00", "fitid": "f1", "memo": "X"})
        form = self.post_form(texto.encode("utf-8"), modo="QUALQUER")

        self.assertFalse(form.is_valid())
        self.assertIn("modo", form.errors)


class ImportacaoViewsEdgeTests(ImportacaoBase):
    def test_form_get_renderiza_campos(self):
        resposta = self.client.get(reverse("importacao:nubank_cartao"))

        self.assertContains(resposta, "Arquivo OFX")
        self.assertContains(resposta, "Somente itens novos")
        self.assertContains(resposta, "Sobrescrever existentes")

    def test_resultado_sem_sessao_redireciona_para_index(self):
        resposta = self.client.get(reverse("importacao:resultado"))

        self.assertRedirects(resposta, reverse("importacao:index"))

    def test_post_sem_arquivo_reexibe_form_com_erro(self):
        resposta = self.client.post(
            reverse("importacao:nubank_cartao"),
            {"conta": self.conta.id, "modo": MODO_NOVOS},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "form")
        self.assertEqual(Lancamento.objects.count(), 0)

    def test_arquivo_invalido_mostra_erro_no_form(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        arquivo = SimpleUploadedFile("nota.txt", b"isto nao e um ofx")
        resposta = self.client.post(
            reverse("importacao:nubank_cartao"),
            {"arquivo": arquivo, "conta": self.conta.id, "modo": MODO_NOVOS},
        )

        self.assertContains(resposta, "OFX")
        self.assertEqual(Lancamento.objects.count(), 0)
