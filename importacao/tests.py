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


class ImportacaoContaBase(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(
            nome="Nubank Conta", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("1000.00")
        )
        MesAberto.objects.create(ano=2026, mes=7)


class ImportacaoContaTests(ImportacaoContaBase):
    def importar(self, texto, modo=MODO_NOVOS):
        from importacao.services import importar_ofx_nubank_conta

        return importar_ofx_nubank_conta(conta=self.conta, texto=texto, modo=modo)

    def test_debit_vira_gasto_variavel_pago(self):
        texto = ofx({"data": "20260701", "valor": "-80.72", "fitid": "c1", "memo": "Compra no debito - NG MAN YAM"})
        resumo = self.importar(texto)

        self.assertEqual(len(resumo["criados"]), 1)
        lanc = Lancamento.objects.get()
        self.assertEqual(lanc.tipo, Lancamento.Tipo.GASTO_VARIAVEL)
        self.assertEqual(lanc.valor, Decimal("80.72"))
        self.assertEqual(lanc.data_vencimento, date(2026, 7, 1))
        self.assertEqual(lanc.data_pagamento, date(2026, 7, 1))
        self.assertEqual(lanc.status, Lancamento.Status.PAGO)
        self.assertEqual((lanc.competencia_ano, lanc.competencia_mes), (2026, 7))
        self.assertTrue(lanc.gerado_automaticamente)

    def test_credit_vira_recebimento_excepcional_pago(self):
        texto = ofx({"data": "20260702", "valor": "432.00", "fitid": "c2", "memo": "Transferencia recebida pelo Pix", "trntype": "CREDIT"})
        self.importar(texto)

        lanc = Lancamento.objects.get()
        self.assertEqual(lanc.tipo, Lancamento.Tipo.RECEBIMENTO_EXCEPCIONAL)
        self.assertEqual(lanc.valor, Decimal("432.00"))
        self.assertEqual(lanc.status, Lancamento.Status.PAGO)

    def test_pagamento_de_fatura_debit_pulado(self):
        texto = ofx({"data": "20260704", "valor": "-18542.10", "fitid": "c3", "memo": "Pagamento de fatura"})
        resumo = self.importar(texto)

        self.assertEqual(Lancamento.objects.count(), 0)
        self.assertEqual(resumo["pulados"][0]["motivo"], "pagamento de fatura")

    def test_pagamento_de_fatura_credit_nao_e_pulado(self):
        texto = ofx({"data": "20260704", "valor": "10.00", "fitid": "c4", "memo": "Pagamento de fatura", "trntype": "CREDIT"})
        resumo = self.importar(texto)

        self.assertEqual(len(resumo["criados"]), 1)
        self.assertEqual(Lancamento.objects.count(), 1)

    def test_memo_de_parcela_nao_cria_compra_parcelada(self):
        texto = ofx({"data": "20260701", "valor": "-100.00", "fitid": "c5", "memo": "Loja X - Parcela 2/3"})
        self.importar(texto)

        lanc = Lancamento.objects.get()
        self.assertEqual(lanc.tipo, Lancamento.Tipo.GASTO_VARIAVEL)
        self.assertEqual(CompraParcelada.objects.count(), 0)
        self.assertIsNone(lanc.parcela_atual)

    def test_reimportacao_idempotente(self):
        texto = ofx({"data": "20260701", "valor": "-80.72", "fitid": "c1", "memo": "Compra no debito"})
        self.importar(texto)
        resumo = self.importar(texto)

        self.assertEqual(Lancamento.objects.count(), 1)
        self.assertEqual(len(resumo["criados"]), 0)
        self.assertEqual(resumo["pulados"][0]["motivo"], "ja importado")

    def test_sobrescrever_reporta_ja_pago_sem_alterar(self):
        texto = ofx({"data": "20260701", "valor": "-80.72", "fitid": "c1", "memo": "Compra no debito"})
        self.importar(texto)
        resumo = self.importar(texto, modo=MODO_SOBRESCREVER)

        lanc = Lancamento.objects.get()
        self.assertEqual(lanc.valor, Decimal("80.72"))
        self.assertEqual(len(resumo["atualizados"]), 0)
        self.assertEqual(resumo["pulados"][0]["motivo"], "ja pago")

    def test_lancamento_excluido_reportado(self):
        texto = ofx({"data": "20260701", "valor": "-80.72", "fitid": "c1", "memo": "Compra no debito"})
        self.importar(texto)
        Lancamento.objects.get().delete()

        resumo = self.importar(texto, modo=MODO_SOBRESCREVER)

        self.assertEqual(Lancamento.objects.count(), 0)
        self.assertEqual(resumo["pulados"][0]["motivo"], "lancamento original excluido")

    def test_mes_fechado_cancela_importacao(self):
        texto = ofx(
            {"data": "20260701", "valor": "-80.72", "fitid": "c1", "memo": "Aberto"},
            {"data": "20260601", "valor": "-10.00", "fitid": "c6", "memo": "Fechado"},
        )
        with self.assertRaises(ValidationError) as ctx:
            self.importar(texto)

        self.assertIn("06/2026", " ".join(ctx.exception.messages))
        self.assertEqual(Lancamento.objects.count(), 0)
        self.assertEqual(ItemImportado.objects.count(), 0)

    def test_modo_invalido_rejeitado(self):
        texto = ofx({"data": "20260701", "valor": "-80.72", "fitid": "c1", "memo": "X"})
        with self.assertRaises(ValidationError):
            self.importar(texto, modo="QUALQUER")


class ImportacaoContaFormTests(ImportacaoContaBase):
    def test_conta_cartao_rejeitada(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from importacao.forms import ImportacaoOFXNubankContaForm

        cartao = Conta.objects.create(nome="Cartao Y", tipo=Conta.Tipo.CARTAO, dia_vencimento=8)
        texto = ofx({"data": "20260701", "valor": "-10.00", "fitid": "c1", "memo": "X"})
        form = ImportacaoOFXNubankContaForm(
            {"conta": cartao.id, "modo": MODO_NOVOS},
            {"arquivo": SimpleUploadedFile("extrato.ofx", texto.encode("utf-8"))},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("conta", form.errors)

    def test_decodifica_utf8_e_cp1252(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from importacao.forms import ImportacaoOFXNubankContaForm

        texto = ofx({"data": "20260701", "valor": "-10.00", "fitid": "c1", "memo": "Transferência São João"})
        for encoding in ("utf-8", "cp1252"):
            form = ImportacaoOFXNubankContaForm(
                {"conta": self.conta.id, "modo": MODO_NOVOS},
                {"arquivo": SimpleUploadedFile("extrato.ofx", texto.encode(encoding))},
            )
            self.assertTrue(form.is_valid(), form.errors)
            self.assertIn("Transferência São João", form.cleaned_data["texto"])


class ImportacaoContaViewsTests(ImportacaoContaBase):
    def test_index_lista_opcao_conta(self):
        resposta = self.client.get(reverse("importacao:index"))
        self.assertContains(resposta, "OFX da conta Nubank")

    def test_form_get_renderiza(self):
        resposta = self.client.get(reverse("importacao:nubank_conta"))

        self.assertContains(resposta, "Importar OFX da conta Nubank")
        self.assertContains(resposta, "Conta corrente")

    def test_fluxo_upload_completo(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        texto = ofx({"data": "20260701", "valor": "-80.72", "fitid": "c1", "memo": "Compra no debito - NG MAN YAM"})
        arquivo = SimpleUploadedFile("extrato.ofx", texto.encode("utf-8"))
        resposta = self.client.post(
            reverse("importacao:nubank_conta"),
            {"arquivo": arquivo, "conta": self.conta.id, "modo": MODO_NOVOS},
            follow=True,
        )

        self.assertContains(resposta, "Resultado da importacao")
        self.assertContains(resposta, "NG MAN YAM")
        self.assertEqual(Lancamento.objects.count(), 1)

    def test_erro_mes_fechado_aparece_no_form(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        texto = ofx({"data": "20260601", "valor": "-10.00", "fitid": "c9", "memo": "Fechado"})
        arquivo = SimpleUploadedFile("extrato.ofx", texto.encode("utf-8"))
        resposta = self.client.post(
            reverse("importacao:nubank_conta"),
            {"arquivo": arquivo, "conta": self.conta.id, "modo": MODO_NOVOS},
        )

        self.assertContains(resposta, "06/2026")
        self.assertEqual(Lancamento.objects.count(), 0)


class ImportacaoContaEdgeTests(ImportacaoContaBase):
    def importar(self, texto, modo=MODO_NOVOS):
        from importacao.services import importar_ofx_nubank_conta

        return importar_ofx_nubank_conta(conta=self.conta, texto=texto, modo=modo)

    def test_sobrescrever_corrige_item_com_pagamento_desmarcado(self):
        texto = ofx({"data": "20260701", "valor": "-80.72", "fitid": "c1", "memo": "Compra no debito"})
        self.importar(texto)

        lanc = Lancamento.objects.get()
        lanc.data_pagamento = None
        lanc.valor = Decimal("50.00")
        lanc.save()

        texto_corrigido = ofx({"data": "20260702", "valor": "-80.72", "fitid": "c1", "memo": "Compra no debito"})
        resumo = self.importar(texto_corrigido, modo=MODO_SOBRESCREVER)

        lanc.refresh_from_db()
        self.assertEqual(lanc.valor, Decimal("80.72"))
        self.assertEqual(lanc.data_vencimento, date(2026, 7, 2))
        self.assertEqual(lanc.data_pagamento, date(2026, 7, 2))
        self.assertEqual(resumo["atualizados"][0]["motivo"], "corrigido pelo extrato")

    def test_transacoes_em_dois_meses_abertos_cada_uma_na_sua_competencia(self):
        MesAberto.objects.create(ano=2026, mes=8)
        texto = ofx(
            {"data": "20260731", "valor": "-10.00", "fitid": "c1", "memo": "Julho"},
            {"data": "20260801", "valor": "-20.00", "fitid": "c2", "memo": "Agosto"},
        )
        self.importar(texto)

        julho = Lancamento.objects.get(descricao="Julho")
        agosto = Lancamento.objects.get(descricao="Agosto")
        self.assertEqual((julho.competencia_ano, julho.competencia_mes), (2026, 7))
        self.assertEqual((agosto.competencia_ano, agosto.competencia_mes), (2026, 8))

    def test_resumo_contem_acctid_do_arquivo(self):
        texto = ofx({"data": "20260701", "valor": "-10.00", "fitid": "c1", "memo": "X"})
        resumo = self.importar(texto)

        self.assertEqual(resumo["acctid"], "acct-uuid-nubank")
        self.assertEqual(ItemImportado.objects.get().acctid, "acct-uuid-nubank")

    def test_memo_com_acentos_preservado(self):
        texto = ofx({"data": "20260701", "valor": "-10.00", "fitid": "c1", "memo": "Transferência enviada pelo Pix - São João"})
        self.importar(texto)

        lanc = Lancamento.objects.get()
        self.assertEqual(lanc.descricao, "Transferência enviada pelo Pix - São João")

    def test_varios_meses_fechados_listados_ordenados(self):
        texto = ofx(
            {"data": "20260501", "valor": "-1.00", "fitid": "c1", "memo": "Maio"},
            {"data": "20260401", "valor": "-2.00", "fitid": "c2", "memo": "Abril"},
        )
        with self.assertRaises(ValidationError) as ctx:
            self.importar(texto)

        mensagem = " ".join(ctx.exception.messages)
        self.assertIn("04/2026, 05/2026", mensagem)


class ValidarMesesAbertosTests(TestCase):
    def test_vazio_nao_levanta(self):
        from importacao.services import _validar_meses_abertos

        _validar_meses_abertos(set())

    def test_meses_formatados_na_mensagem(self):
        from importacao.services import _validar_meses_abertos

        with self.assertRaises(ValidationError) as ctx:
            _validar_meses_abertos({(2026, 6), (2025, 12)})

        self.assertIn("12/2025, 06/2026", " ".join(ctx.exception.messages))


class ImportacaoContaFormEdgeTests(ImportacaoContaBase):
    def test_modo_invalido_rejeitado_na_base(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from importacao.forms import ImportacaoOFXNubankContaForm

        texto = ofx({"data": "20260701", "valor": "-10.00", "fitid": "c1", "memo": "X"})
        form = ImportacaoOFXNubankContaForm(
            {"conta": self.conta.id, "modo": "QUALQUER"},
            {"arquivo": SimpleUploadedFile("extrato.ofx", texto.encode("utf-8"))},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("modo", form.errors)


class ImportacaoIndexTests(ImportacaoContaBase):
    def test_index_mostra_as_duas_opcoes(self):
        resposta = self.client.get(reverse("importacao:index"))

        self.assertContains(resposta, "OFX do cartao Nubank")
        self.assertContains(resposta, "OFX da conta Nubank")

    def test_post_sem_arquivo_reexibe_form_da_conta(self):
        resposta = self.client.post(
            reverse("importacao:nubank_conta"),
            {"conta": self.conta.id, "modo": MODO_NOVOS},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Lancamento.objects.count(), 0)


def ofx_com_secao(secao, *transacoes):
    return ofx(*transacoes).replace("<BANKTRANLIST>", f"<{secao}>\n<BANKTRANLIST>")


class CorrecoesReviewTests(TestCase):
    """Regressoes dos achados do code review da importacao de conta."""

    def setUp(self):
        self.cartao = Conta.objects.create(nome="Cartao R", tipo=Conta.Tipo.CARTAO, dia_vencimento=8)
        self.banco = Conta.objects.create(nome="Banco R", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("0.00"))
        MesAberto.objects.create(ano=2026, mes=7)

    def importar_conta(self, texto, modo=MODO_NOVOS, conta=None):
        from importacao.services import importar_ofx_nubank_conta

        return importar_ofx_nubank_conta(conta=conta or self.banco, texto=texto, modo=modo)

    def importar_cartao(self, texto, modo=MODO_NOVOS):
        return importar_ofx_nubank_cartao(conta=self.cartao, texto=texto, modo=modo)

    # Achado 1: arquivo do tipo errado rejeitado nas duas telas
    def test_fatura_de_cartao_rejeitada_na_importacao_de_conta(self):
        texto = ofx_com_secao("CCSTMTRS", {"data": "20260719", "valor": "-10.00", "fitid": "f1", "memo": "X"})
        with self.assertRaises(ValidationError) as ctx:
            self.importar_conta(texto)

        self.assertIn("fatura de cartao", " ".join(ctx.exception.messages))
        self.assertEqual(Lancamento.objects.count(), 0)

    def test_extrato_de_conta_rejeitado_na_importacao_de_cartao(self):
        texto = ofx_com_secao("STMTRS", {"data": "20260719", "valor": "-10.00", "fitid": "f1", "memo": "X"})
        with self.assertRaises(ValidationError) as ctx:
            self.importar_cartao(texto)

        self.assertIn("extrato de conta corrente", " ".join(ctx.exception.messages))
        self.assertEqual(Lancamento.objects.count(), 0)

    def test_acctid_divergente_rejeitado(self):
        texto1 = ofx({"data": "20260719", "valor": "-10.00", "fitid": "f1", "memo": "X"})
        self.importar_conta(texto1)

        texto2 = ofx({"data": "20260719", "valor": "-20.00", "fitid": "f2", "memo": "Y"}).replace(
            "acct-uuid-nubank", "outro-acctid"
        )
        with self.assertRaises(ValidationError) as ctx:
            self.importar_conta(texto2)

        self.assertIn("ACCTID", " ".join(ctx.exception.messages))
        self.assertEqual(Lancamento.objects.count(), 1)

    # Achado 2: direcao pelo sinal de TRNAMT, nao pelo TRNTYPE
    def test_trntype_desconhecido_com_valor_positivo_vira_recebimento(self):
        texto = ofx({"data": "20260719", "valor": "432.00", "fitid": "f1", "memo": "Entrada", "trntype": "XFER"})
        self.importar_conta(texto)

        lanc = Lancamento.objects.get()
        self.assertEqual(lanc.tipo, Lancamento.Tipo.RECEBIMENTO_EXCEPCIONAL)

    def test_trntype_desconhecido_com_valor_negativo_vira_gasto(self):
        texto = ofx({"data": "20260719", "valor": "-50.00", "fitid": "f1", "memo": "Saida", "trntype": "OTHER"})
        self.importar_cartao(texto)

        lanc = Lancamento.objects.get()
        self.assertEqual(lanc.tipo, Lancamento.Tipo.GASTO_VARIAVEL)

    # Achado 4: valor zero pulado sem abortar o import
    def test_valor_zero_pulado_sem_abortar(self):
        texto = ofx(
            {"data": "20260719", "valor": "0.00", "fitid": "f1", "memo": "Ajuste"},
            {"data": "20260719", "valor": "-10.00", "fitid": "f2", "memo": "Compra"},
        )
        resumo = self.importar_conta(texto)

        self.assertEqual(len(resumo["criados"]), 1)
        self.assertEqual(resumo["pulados"][0]["motivo"], "valor zero")
        self.assertEqual(Lancamento.objects.count(), 1)

    # Achado 5: sobrescrever nao move lancamento para mes fechado
    def test_sobrescrever_nao_move_para_mes_fechado(self):
        texto1 = ofx({"data": "20260719", "valor": "-10.00", "fitid": "f1", "memo": "Compra"})
        self.importar_conta(texto1)
        lanc = Lancamento.objects.get()
        lanc.data_pagamento = None
        lanc.save()

        texto2 = ofx({"data": "20260619", "valor": "-10.00", "fitid": "f1", "memo": "Compra"})
        with self.assertRaises(ValidationError) as ctx:
            self.importar_conta(texto2, modo=MODO_SOBRESCREVER)

        self.assertIn("06/2026", " ".join(ctx.exception.messages))
        lanc.refresh_from_db()
        self.assertEqual(lanc.competencia_mes, 7)

    # Achado 3: sem_mudanca no fluxo da conta (sem correcao fantasma)
    def test_reimportar_sobrescrever_apos_correcao_reporta_ja_pago(self):
        texto = ofx({"data": "20260719", "valor": "-10.00", "fitid": "f1", "memo": "Compra"})
        self.importar_conta(texto)
        lanc = Lancamento.objects.get()
        lanc.data_pagamento = None
        lanc.save()

        r1 = self.importar_conta(texto, modo=MODO_SOBRESCREVER)
        self.assertEqual(r1["atualizados"][0]["motivo"], "corrigido pelo extrato")

        r2 = self.importar_conta(texto, modo=MODO_SOBRESCREVER)
        self.assertEqual(len(r2["atualizados"]), 0)
        self.assertEqual(r2["pulados"][0]["motivo"], "ja pago")

    # Achado 8: guard de fatura tolera sufixo novo do banco
    def test_pagamento_de_fatura_com_sufixo_pulado(self):
        texto = ofx({"data": "20260704", "valor": "-100.00", "fitid": "f1", "memo": "Pagamento de fatura - Cartao Nubank"})
        resumo = self.importar_conta(texto)

        self.assertEqual(Lancamento.objects.count(), 0)
        self.assertEqual(resumo["pulados"][0]["motivo"], "pagamento de fatura")

    def test_pagamento_recebido_com_sufixo_pulado_no_cartao(self):
        texto = ofx({"data": "20260704", "valor": "100.00", "fitid": "f1", "memo": "Pagamento recebido - fatura", "trntype": "CREDIT"})
        resumo = self.importar_cartao(texto)

        self.assertEqual(Lancamento.objects.count(), 0)
        self.assertEqual(resumo["pulados"][0]["motivo"], "pagamento de fatura")

    # Dedup dentro do mesmo arquivo nao explode em IntegrityError
    def test_chave_duplicada_no_mesmo_arquivo_pulada(self):
        texto = ofx(
            {"data": "20260719", "valor": "-10.00", "fitid": "f1", "memo": "Compra"},
            {"data": "20260719", "valor": "-10.00", "fitid": "f1", "memo": "Compra"},
        )
        resumo = self.importar_conta(texto)

        self.assertEqual(Lancamento.objects.count(), 1)
        self.assertEqual(resumo["pulados"][0]["motivo"], "duplicado no arquivo")

    # Achado 6: arquivo indecodificavel vira erro de form, nao 500
    def test_arquivo_indecodificavel_da_erro_de_validacao(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from importacao.forms import ImportacaoOFXNubankContaForm

        form = ImportacaoOFXNubankContaForm(
            {"conta": self.banco.id, "modo": MODO_NOVOS},
            {"arquivo": SimpleUploadedFile("lixo.ofx", b"\x81\x8d\x8f\x90\x9d")},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("arquivo", form.errors)

    # Bug achado no smoke: compra por fitid deve ser escopada por conta
    def test_mesmo_fitid_em_outra_conta_cria_compra_propria(self):
        cartao2 = Conta.objects.create(nome="Cartao R2", tipo=Conta.Tipo.CARTAO, dia_vencimento=8)
        texto = ofx({"data": "20260714", "valor": "-296.68", "fitid": "fdup", "memo": "Idoc3d - Parcela 1/3"})

        importar_ofx_nubank_cartao(conta=self.cartao, texto=texto, modo=MODO_NOVOS)
        importar_ofx_nubank_cartao(conta=cartao2, texto=texto, modo=MODO_NOVOS)

        self.assertEqual(CompraParcelada.objects.filter(fitid="fdup").count(), 2)
        self.assertEqual(Lancamento.objects.filter(conta=self.cartao).count(), 3)
        self.assertEqual(Lancamento.objects.filter(conta=cartao2).count(), 3)


class ResumirMemoTests(TestCase):
    def test_memo_pix_completo_corta_em_operacao_e_contraparte(self):
        from importacao.services import resumir_memo

        memo = (
            "Transferência enviada pelo Pix - CAPITALGAS COMERCIO DE GAS LTDA - "
            "02.150.689/0001-66 - COOP SICREDI CAMPOS GERAIS Agência: 730 Conta: 24121-5"
        )
        descricao, detalhes = resumir_memo(memo)

        self.assertEqual(descricao, "Transferência enviada pelo Pix - CAPITALGAS COMERCIO DE GAS LTDA")
        self.assertEqual(detalhes, memo)

    def test_memo_curto_fica_intacto_sem_detalhes(self):
        from importacao.services import resumir_memo

        descricao, detalhes = resumir_memo("Compra no débito - NG MAN YAM")

        self.assertEqual(descricao, "Compra no débito - NG MAN YAM")
        self.assertEqual(detalhes, "")

    def test_memo_sem_separador_maior_que_limite_e_truncado(self):
        from importacao.services import resumir_memo

        memo = "X" * 200
        descricao, detalhes = resumir_memo(memo)

        self.assertEqual(len(descricao), 180)
        self.assertTrue(descricao.endswith("…"))
        self.assertEqual(detalhes, memo)

    def test_contraparte_gigante_respeita_max_da_descricao(self):
        from importacao.services import resumir_memo

        memo = "Transferência enviada pelo Pix - " + "N" * 200 + " - doc - banco"
        descricao, detalhes = resumir_memo(memo)

        self.assertLessEqual(len(descricao), 180)
        self.assertEqual(detalhes, memo)


class ImportacaoDetalhesTests(ImportacaoContaBase):
    def test_import_conta_encurta_descricao_e_guarda_memo_em_detalhes(self):
        from importacao.services import importar_ofx_nubank_conta

        memo = (
            "Transferência enviada pelo Pix - CAPITALGAS COMERCIO DE GAS LTDA - "
            "02.150.689/0001-66 - COOP SICREDI Agência: 730 Conta: 24121-5"
        )
        texto = ofx({"data": "20260710", "valor": "-432.71", "fitid": "c1", "memo": memo})
        resumo = importar_ofx_nubank_conta(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        lanc = Lancamento.objects.get()
        self.assertEqual(lanc.descricao, "Transferência enviada pelo Pix - CAPITALGAS COMERCIO DE GAS LTDA")
        self.assertEqual(lanc.detalhes, memo)
        self.assertEqual(resumo["criados"][0]["descricao"], lanc.descricao)

    def test_memo_curto_nao_preenche_detalhes(self):
        from importacao.services import importar_ofx_nubank_conta

        texto = ofx({"data": "20260710", "valor": "-16.00", "fitid": "c2", "memo": "Compra no débito - GARAGEM"})
        importar_ofx_nubank_conta(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        lanc = Lancamento.objects.get()
        self.assertEqual(lanc.descricao, "Compra no débito - GARAGEM")
        self.assertEqual(lanc.detalhes, "")

    def test_dedup_continua_usando_memo_completo(self):
        from importacao.services import importar_ofx_nubank_conta

        memo = "Transferência enviada pelo Pix - FULANO - •••.111.222-•• - BANCO X Agência: 1 Conta: 2"
        texto = ofx({"data": "20260710", "valor": "-10.00", "fitid": "c3", "memo": memo})
        importar_ofx_nubank_conta(conta=self.conta, texto=texto, modo=MODO_NOVOS)
        resumo = importar_ofx_nubank_conta(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        self.assertEqual(Lancamento.objects.count(), 1)
        self.assertEqual(resumo["pulados"][0]["motivo"], "ja importado")


class LancamentoFormDetalhesTests(TestCase):
    def test_form_de_lancamento_tem_campo_detalhes_opcional(self):
        from lancamentos.forms import LancamentoForm

        form = LancamentoForm()
        self.assertIn("detalhes", form.fields)
        self.assertFalse(form.fields["detalhes"].required)


class ComContextoErroTests(ImportacaoContaBase):
    def test_erro_de_validacao_nomeia_transacao_ofensora(self):
        from importacao.services import importar_ofx_nubank_conta

        investimento = Conta.objects.create(
            nome="Invest R", tipo=Conta.Tipo.INVESTIMENTO, saldo_atual=Decimal("0.00")
        )
        texto = ofx({"data": "20260710", "valor": "-10.00", "fitid": "c1", "memo": "Compra proibida"})

        with self.assertRaises(ValidationError) as ctx:
            importar_ofx_nubank_conta(conta=investimento, texto=texto, modo=MODO_NOVOS)

        mensagem = " ".join(ctx.exception.messages)
        self.assertIn("Compra proibida", mensagem)
        self.assertIn("10/07/2026", mensagem)
        self.assertEqual(Lancamento.objects.count(), 0)


class CartaoZeroEDuplicadoTests(ImportacaoBase):
    def test_valor_zero_pulado_no_cartao(self):
        texto = ofx(
            {"data": "20260719", "valor": "0.00", "fitid": "f1", "memo": "Ajuste"},
            {"data": "20260719", "valor": "-10.00", "fitid": "f2", "memo": "Compra"},
        )
        resumo = importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        self.assertEqual(len(resumo["criados"]), 1)
        self.assertEqual(resumo["pulados"][0]["motivo"], "valor zero")

    def test_chave_duplicada_no_mesmo_arquivo_pulada_no_cartao(self):
        texto = ofx(
            {"data": "20260719", "valor": "-10.00", "fitid": "f1", "memo": "Compra"},
            {"data": "20260719", "valor": "-10.00", "fitid": "f1", "memo": "Compra"},
        )
        resumo = importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        self.assertEqual(Lancamento.objects.count(), 1)
        self.assertEqual(resumo["pulados"][0]["motivo"], "duplicado no arquivo")

    def test_arquivo_sem_acctid_importa_normalmente(self):
        texto = ofx({"data": "20260719", "valor": "-10.00", "fitid": "f1", "memo": "Compra"}).replace(
            "<ACCTID>acct-uuid-nubank</ACCTID>", ""
        )
        resumo = importar_ofx_nubank_cartao(conta=self.conta, texto=texto, modo=MODO_NOVOS)

        self.assertEqual(len(resumo["criados"]), 1)
        self.assertEqual(resumo["acctid"], "")


class MigracaoEncurtarDescricoesTests(TestCase):
    def _modulo(self):
        import importlib

        return importlib.import_module("importacao.migrations.0002_encurtar_descricoes_importadas")

    def setUp(self):
        from django.apps import apps as django_apps

        self.apps = django_apps
        self.banco = Conta.objects.create(nome="Banco M", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("0.00"))
        self.memo = (
            "Transferência enviada pelo Pix - CAPITALGAS COMERCIO DE GAS LTDA - "
            "02.150.689/0001-66 - COOP SICREDI Agência: 730 Conta: 24121-5"
        )
        self.lanc = Lancamento.objects.create(
            descricao=self.memo,
            tipo=Lancamento.Tipo.GASTO_VARIAVEL,
            data_vencimento=date(2026, 7, 10),
            data_pagamento=date(2026, 7, 10),
            valor=Decimal("432.71"),
            conta=self.banco,
            competencia_ano=2026,
            competencia_mes=7,
            gerado_automaticamente=True,
        )
        ItemImportado.objects.create(conta=self.banco, fitid="m1", chave_dedup="km1", lancamento=self.lanc)

    def test_backfill_encurta_e_preserva_memo(self):
        modulo = self._modulo()
        modulo.encurtar_descricoes(self.apps, None)

        self.lanc.refresh_from_db()
        self.assertEqual(
            self.lanc.descricao, "Transferência enviada pelo Pix - CAPITALGAS COMERCIO DE GAS LTDA"
        )
        self.assertEqual(self.lanc.detalhes, self.memo)

    def test_backfill_e_idempotente_e_reversivel(self):
        modulo = self._modulo()
        modulo.encurtar_descricoes(self.apps, None)
        modulo.encurtar_descricoes(self.apps, None)

        self.lanc.refresh_from_db()
        descricao_curta = self.lanc.descricao
        self.assertEqual(self.lanc.detalhes, self.memo)

        modulo.reverter(self.apps, None)
        self.lanc.refresh_from_db()
        self.assertEqual(self.lanc.descricao, self.memo)
        self.assertEqual(self.lanc.detalhes, "")
        self.assertNotEqual(self.lanc.descricao, descricao_curta)

    def test_backfill_trunca_descricao_muito_longa(self):
        modulo = self._modulo()
        memo = "X" + " - " + "Y" * 200 + " - RESTANTE"
        # Bypass model validation to simulate legacy data > 180 chars.
        Lancamento.objects.filter(pk=self.lanc.pk).update(descricao=memo)
        modulo.encurtar_descricoes(self.apps, None)

        self.lanc.refresh_from_db()
        self.assertEqual(len(self.lanc.descricao), 180)
        self.assertTrue(self.lanc.descricao.endswith("…"))
        self.assertEqual(self.lanc.detalhes, memo)
        modulo = self._modulo()
        cartao = Conta.objects.create(nome="Cartao M", tipo=Conta.Tipo.CARTAO, dia_vencimento=8)
        lanc_cartao = Lancamento.objects.create(
            descricao="A - B - C - D",
            tipo=Lancamento.Tipo.GASTO_VARIAVEL,
            data_vencimento=date(2026, 7, 8),
            valor=Decimal("10.00"),
            conta=cartao,
            competencia_ano=2026,
            competencia_mes=7,
            gerado_automaticamente=True,
        )
        ItemImportado.objects.create(conta=cartao, fitid="m2", chave_dedup="km2", lancamento=lanc_cartao)
        curto = Lancamento.objects.create(
            descricao="Compra no débito - GARAGEM",
            tipo=Lancamento.Tipo.GASTO_VARIAVEL,
            data_vencimento=date(2026, 7, 10),
            valor=Decimal("5.00"),
            conta=self.banco,
            competencia_ano=2026,
            competencia_mes=7,
            gerado_automaticamente=True,
        )
        ItemImportado.objects.create(conta=self.banco, fitid="m3", chave_dedup="km3", lancamento=curto)

        modulo.encurtar_descricoes(self.apps, None)

        lanc_cartao.refresh_from_db()
        curto.refresh_from_db()
        self.assertEqual(lanc_cartao.descricao, "A - B - C - D")
        self.assertEqual(lanc_cartao.detalhes, "")
        self.assertEqual(curto.descricao, "Compra no débito - GARAGEM")
        self.assertEqual(curto.detalhes, "")


class FluxoViewSobrescreverTests(ImportacaoContaBase):
    def test_upload_sobrescrever_mostra_atualizados_no_resultado(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        texto = ofx({"data": "20260710", "valor": "-50.00", "fitid": "v1", "memo": "Compra no débito - LOJA"})
        self.client.post(
            reverse("importacao:nubank_conta"),
            {"arquivo": SimpleUploadedFile("e.ofx", texto.encode("utf-8")), "conta": self.conta.id, "modo": MODO_NOVOS},
        )
        lanc = Lancamento.objects.get()
        lanc.data_pagamento = None
        lanc.save()

        resposta = self.client.post(
            reverse("importacao:nubank_conta"),
            {
                "arquivo": SimpleUploadedFile("e.ofx", texto.encode("utf-8")),
                "conta": self.conta.id,
                "modo": MODO_SOBRESCREVER,
            },
            follow=True,
        )

        self.assertContains(resposta, "corrigido pelo extrato")
        lanc.refresh_from_db()
        self.assertEqual(lanc.data_pagamento, date(2026, 7, 10))


class TabelaItensDescricaoTests(TestCase):
    def test_descricao_com_separador_gera_linha_secundaria(self):
        from django.template.loader import render_to_string

        html = render_to_string(
            "importacao/_tabela_itens.html",
            {
                "itens": [
                    {
                        "descricao": "Pix enviado - Fulano de Tal",
                        "valor": Decimal("10.00"),
                        "competencia": "7/2026",
                        "motivo": "",
                    }
                ],
                "vazio": "Nada.",
            },
        )
        self.assertIn(
            '<span class="m3-descricao-secundaria">Fulano de Tal</span>', html
        )
