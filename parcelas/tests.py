from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from contas.models import Conta
from lancamentos.models import Lancamento
from parcelas.models import CompraParcelada
from parcelas.services import (
    criar_parcela_importada,
    gerar_parcelas_da_compra,
    registrar_compra_importada,
)


class ParcelasTests(TestCase):
    def test_gera_parcelas_com_vencimento_e_descricao(self):
        conta = Conta.objects.create(
            nome="Cartao XPTO",
            tipo=Conta.Tipo.CARTAO,
            dia_vencimento=10,
        )

        gerar_parcelas_da_compra(
            descricao="Compra de notebook",
            valor_total=Decimal("100.00"),
            total_parcelas=10,
            conta=conta,
            data_compra=date(2026, 1, 15),
        )

        parcelas = Lancamento.objects.filter(tipo=Lancamento.Tipo.PARCELA_CARTAO).order_by("parcela_atual")
        self.assertEqual(parcelas.count(), 10)
        self.assertEqual(parcelas.first().descricao, "Compra de notebook 1/10")
        self.assertEqual(parcelas.first().data_vencimento, date(2026, 2, 10))
        self.assertEqual(parcelas.first().competencia_ano, 2026)
        self.assertEqual(parcelas.first().competencia_mes, 2)
        self.assertEqual(parcelas.last().descricao, "Compra de notebook 10/10")
        self.assertEqual(parcelas.last().data_vencimento, date(2026, 11, 10))
        self.assertEqual(parcelas.last().competencia_ano, 2026)
        self.assertEqual(parcelas.last().competencia_mes, 11)

    def test_gera_somente_parcelas_restantes_quando_ha_parcelas_pagas(self):
        conta = Conta.objects.create(
            nome="Cartao Restante",
            tipo=Conta.Tipo.CARTAO,
            dia_vencimento=10,
        )

        gerar_parcelas_da_compra(
            descricao="Compra de notebook",
            valor_total=Decimal("1000.00"),
            total_parcelas=10,
            parcelas_pagas=5,
            conta=conta,
            data_compra=date(2026, 6, 25),
        )

        parcelas = Lancamento.objects.filter(tipo=Lancamento.Tipo.PARCELA_CARTAO).order_by("parcela_atual")
        self.assertEqual(parcelas.count(), 5)
        self.assertEqual(parcelas.first().descricao, "Compra de notebook 6/10")
        self.assertEqual(parcelas.first().parcela_atual, 6)
        self.assertEqual(parcelas.first().competencia_ano, 2026)
        self.assertEqual(parcelas.first().competencia_mes, 7)
        self.assertEqual(parcelas.first().data_vencimento, date(2026, 7, 10))
        self.assertEqual(parcelas.last().descricao, "Compra de notebook 10/10")
        self.assertEqual(parcelas.last().parcela_atual, 10)
        self.assertEqual(parcelas.last().competencia_ano, 2026)
        self.assertEqual(parcelas.last().competencia_mes, 11)
        self.assertEqual(parcelas.last().data_vencimento, date(2026, 11, 10))
        self.assertEqual(
            [(p.competencia_ano, p.competencia_mes) for p in parcelas],
            [(2026, 7), (2026, 8), (2026, 9), (2026, 10), (2026, 11)],
        )

    def test_rejeita_quando_todas_parcelas_ja_foram_pagas(self):
        conta = Conta.objects.create(
            nome="Cartao Completo",
            tipo=Conta.Tipo.CARTAO,
            dia_vencimento=10,
        )

        with self.assertRaises(ValidationError):
            gerar_parcelas_da_compra(
                descricao="Compra quitada",
                valor_total=Decimal("100.00"),
                total_parcelas=10,
                parcelas_pagas=10,
                conta=conta,
                data_compra=date(2026, 1, 15),
            )

        self.assertEqual(CompraParcelada.objects.count(), 0)
        self.assertEqual(Lancamento.objects.filter(tipo=Lancamento.Tipo.PARCELA_CARTAO).count(), 0)

    def test_rejeita_quando_parcelas_pagas_fora_da_faixa(self):
        conta = Conta.objects.create(
            nome="Cartao Faixa",
            tipo=Conta.Tipo.CARTAO,
            dia_vencimento=10,
        )

        with self.assertRaises(ValidationError):
            gerar_parcelas_da_compra(
                descricao="Compra invalida negativo",
                valor_total=Decimal("100.00"),
                total_parcelas=10,
                parcelas_pagas=-1,
                conta=conta,
                data_compra=date(2026, 1, 15),
            )

        with self.assertRaises(ValidationError):
            gerar_parcelas_da_compra(
                descricao="Compra invalida acima",
                valor_total=Decimal("100.00"),
                total_parcelas=10,
                parcelas_pagas=11,
                conta=conta,
                data_compra=date(2026, 1, 15),
            )

        self.assertEqual(CompraParcelada.objects.count(), 0)
        self.assertEqual(Lancamento.objects.filter(tipo=Lancamento.Tipo.PARCELA_CARTAO).count(), 0)


class RegistrarCompraImportadaTests(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(
            nome="Cartao Import",
            tipo=Conta.Tipo.CARTAO,
            dia_vencimento=8,
        )

    def registrar(self, **kwargs):
        params = {
            "descricao": "Idoc3d",
            "valor_parcela": Decimal("296.68"),
            "parcela_atual": 1,
            "total_parcelas": 3,
            "conta": self.conta,
            "data_lancamento": date(2026, 7, 14),
            "fitid": "fitid-idoc",
        }
        params.update(kwargs)
        return registrar_compra_importada(**params)

    def test_cria_compra_com_fitid_e_valor_total_estimado(self):
        compra, parcelas = self.registrar()

        self.assertEqual(compra.fitid, "fitid-idoc")
        self.assertEqual(compra.valor_total, Decimal("890.04"))
        self.assertEqual(compra.total_parcelas, 3)
        self.assertEqual(compra.data_compra, date(2026, 7, 14))
        self.assertEqual(len(parcelas), 3)

    def test_parcela_atual_fica_no_mes_do_lancamento_e_futuras_nos_seguintes(self):
        _, parcelas = self.registrar()

        self.assertEqual(
            [(p.parcela_atual, p.competencia_ano, p.competencia_mes) for p in parcelas],
            [(1, 2026, 7), (2, 2026, 8), (3, 2026, 9)],
        )
        for parcela in parcelas:
            self.assertEqual(parcela.tipo, Lancamento.Tipo.PARCELA_CARTAO)
            self.assertEqual(parcela.valor, Decimal("296.68"))
            self.assertEqual(parcela.conta, self.conta)
            self.assertEqual(parcela.total_parcelas, 3)
            self.assertTrue(parcela.gerado_automaticamente)
        self.assertEqual(parcelas[0].descricao, "Idoc3d 1/3")
        self.assertEqual(parcelas[0].data_vencimento, date(2026, 7, 8))
        self.assertEqual(parcelas[1].data_vencimento, date(2026, 8, 8))

    def test_compra_no_meio_gera_somente_da_parcela_atual_em_diante(self):
        _, parcelas = self.registrar(parcela_atual=4, total_parcelas=12)

        self.assertEqual(len(parcelas), 9)
        self.assertEqual(parcelas[0].parcela_atual, 4)
        self.assertEqual(parcelas[-1].parcela_atual, 12)

    def test_ultima_parcela_gera_uma_so(self):
        _, parcelas = self.registrar(parcela_atual=10, total_parcelas=10)

        self.assertEqual(len(parcelas), 1)
        self.assertEqual(parcelas[0].descricao, "Idoc3d 10/10")

    def test_virada_de_ano_incrementa_competencia_ano(self):
        _, parcelas = self.registrar(data_lancamento=date(2026, 11, 14))

        self.assertEqual(
            [(p.competencia_ano, p.competencia_mes) for p in parcelas],
            [(2026, 11), (2026, 12), (2027, 1)],
        )

    def test_parcela_atual_fora_do_intervalo_rejeitada(self):
        for parcela_atual in (0, 4):
            with self.assertRaises(ValidationError):
                self.registrar(parcela_atual=parcela_atual)

        self.assertEqual(CompraParcelada.objects.count(), 0)
        self.assertEqual(Lancamento.objects.count(), 0)

    def test_fitid_duplicado_rejeitado(self):
        from django.db import IntegrityError, transaction

        self.registrar()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.registrar(descricao="Outra compra")


class CriarParcelaImportadaTests(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(
            nome="Cartao Avulso",
            tipo=Conta.Tipo.CARTAO,
            dia_vencimento=31,
        )
        self.compra = CompraParcelada.objects.create(
            descricao="Compra Existente",
            conta=self.conta,
            valor_total=Decimal("300.00"),
            total_parcelas=3,
            data_compra=date(2026, 1, 15),
            fitid="fitid-existente",
        )

    def test_cria_parcela_com_dados_da_compra(self):
        parcela = criar_parcela_importada(
            compra=self.compra,
            parcela_atual=2,
            valor=Decimal("100.00"),
            competencia_ano=2026,
            competencia_mes=3,
        )

        self.assertEqual(parcela.descricao, "Compra Existente 2/3")
        self.assertEqual(parcela.tipo, Lancamento.Tipo.PARCELA_CARTAO)
        self.assertEqual(parcela.conta, self.conta)
        self.assertEqual(parcela.total_parcelas, 3)
        self.assertEqual(parcela.parcela_atual, 2)
        self.assertTrue(parcela.gerado_automaticamente)

    def test_dia_vencimento_maior_que_ultimo_dia_do_mes_e_ajustado(self):
        parcela = criar_parcela_importada(
            compra=self.compra,
            parcela_atual=2,
            valor=Decimal("100.00"),
            competencia_ano=2026,
            competencia_mes=2,
        )

        self.assertEqual(parcela.data_vencimento, date(2026, 2, 28))


class CompraParceladaModelTests(TestCase):
    def setUp(self):
        self.cartao = Conta.objects.create(
            nome="Cartao Modelo", tipo=Conta.Tipo.CARTAO, dia_vencimento=10
        )
        self.compra = CompraParcelada(
            descricao="TV",
            conta=self.cartao,
            valor_total=Decimal("1200.00"),
            total_parcelas=10,
            data_compra=date(2026, 1, 15),
        )

    def test_str(self):
        self.assertEqual(str(self.compra), "TV (10x)")

    def test_valor_parcela(self):
        self.assertEqual(self.compra.valor_parcela, Decimal("120.00"))

    def test_clean_rejeita_conta_nao_cartao(self):
        banco = Conta.objects.create(nome="Banco", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("0.00"))
        compra = CompraParcelada(
            descricao="Erro",
            conta=banco,
            valor_total=Decimal("100.00"),
            total_parcelas=3,
            data_compra=date(2026, 1, 15),
        )
        with self.assertRaises(ValidationError) as ctx:
            compra.full_clean()
        self.assertIn("conta", ctx.exception.message_dict)

    def test_clean_rejeita_total_parcelas_menor_que_dois(self):
        compra = CompraParcelada(
            descricao="Erro",
            conta=self.cartao,
            valor_total=Decimal("100.00"),
            total_parcelas=1,
            data_compra=date(2026, 1, 15),
        )
        with self.assertRaises(ValidationError) as ctx:
            compra.full_clean()
        self.assertIn("total_parcelas", ctx.exception.message_dict)
