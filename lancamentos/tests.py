from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from contas.models import Conta
from lancamentos.models import Lancamento


class LancamentoStatusTests(TestCase):
    def setUp(self):
        self.conta_banco = Conta.objects.create(
            nome="Banco",
            tipo=Conta.Tipo.BANCO,
            saldo_atual=Decimal("1000.00"),
            limite_negativo=Decimal("200.00"),
        )
        self.conta_inv = Conta.objects.create(
            nome="Invest",
            tipo=Conta.Tipo.INVESTIMENTO,
            saldo_atual=Decimal("5000.00"),
        )

    def test_status_previsto_e_pendente(self):
        hoje = date.today()
        previsto = Lancamento.objects.create(
            descricao="Conta futura",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=hoje,
            valor=Decimal("20.00"),
            conta=self.conta_banco,
            competencia_ano=hoje.year,
            competencia_mes=hoje.month,
        )
        pendente = Lancamento.objects.create(
            descricao="Conta atrasada",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=hoje - timedelta(days=1),
            valor=Decimal("20.00"),
            conta=self.conta_banco,
            competencia_ano=hoje.year,
            competencia_mes=hoje.month,
        )
        self.assertEqual(previsto.status, Lancamento.Status.PREVISTO)
        self.assertEqual(pendente.status, Lancamento.Status.PENDENTE)

    def test_status_pago(self):
        hoje = date.today()
        pago = Lancamento.objects.create(
            descricao="Conta paga",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=hoje + timedelta(days=2),
            data_pagamento=hoje,
            valor=Decimal("10.00"),
            conta=self.conta_banco,
            competencia_ano=hoje.year,
            competencia_mes=hoje.month,
        )
        self.assertEqual(pago.status, Lancamento.Status.PAGO)

    def test_conciliacao_so_automatica(self):
        hoje = date.today()
        with self.assertRaises(ValidationError):
            Lancamento.objects.create(
                descricao="Teste conciliacao",
                tipo=Lancamento.Tipo.CONCILIACAO,
                data_vencimento=hoje,
                valor=Decimal("10.00"),
                conta=self.conta_banco,
                competencia_ano=hoje.year,
                competencia_mes=hoje.month,
            )

    def test_aporte_resgate_so_em_investimento(self):
        hoje = date.today()
        with self.assertRaises(ValidationError):
            Lancamento.objects.create(
                descricao="Aporte invalido",
                tipo=Lancamento.Tipo.APORTE,
                data_vencimento=hoje,
                valor=Decimal("10.00"),
                conta=self.conta_banco,
                competencia_ano=hoje.year,
                competencia_mes=hoje.month,
            )

        valido = Lancamento.objects.create(
            descricao="Aporte valido",
            tipo=Lancamento.Tipo.APORTE,
            data_vencimento=hoje,
            valor=Decimal("10.00"),
            conta=self.conta_inv,
            competencia_ano=hoje.year,
            competencia_mes=hoje.month,
        )
        self.assertEqual(valido.direcao, "ENTRADA")
