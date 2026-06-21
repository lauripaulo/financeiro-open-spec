from datetime import date
from decimal import Decimal

from django.test import TestCase

from contas.models import Conta
from lancamentos.models import Lancamento
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
        self.assertEqual(parcelas.last().descricao, "Compra de notebook 10/10")
        self.assertEqual(parcelas.last().data_vencimento, date(2026, 11, 10))
