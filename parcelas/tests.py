from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from contas.models import Conta
from lancamentos.models import Lancamento
from parcelas.models import CompraParcelada
from parcelas.services import gerar_parcelas_da_compra


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
