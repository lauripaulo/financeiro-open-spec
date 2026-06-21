from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from contas.models import Conta
from lancamentos.models import Lancamento


class ContaModelTests(TestCase):
    def test_banco_exige_saldo_inicial(self):
        conta = Conta(nome="Banco A", tipo=Conta.Tipo.BANCO)
        with self.assertRaises(ValidationError):
            conta.full_clean()

    def test_investimento_exige_saldo_inicial(self):
        conta = Conta(nome="Invest", tipo=Conta.Tipo.INVESTIMENTO)
        with self.assertRaises(ValidationError):
            conta.full_clean()

    def test_exclusao_bloqueada_quando_tem_lancamento(self):
        conta = Conta.objects.create(
            nome="Conta Teste",
            tipo=Conta.Tipo.BANCO,
            saldo_atual=Decimal("100.00"),
            limite_negativo=Decimal("300.00"),
        )
        Lancamento.objects.create(
            descricao="Aluguel",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento="2026-01-10",
            valor=Decimal("50.00"),
            conta=conta,
            competencia_ano=2026,
            competencia_mes=1,
        )

        with self.assertRaises(ValidationError):
            conta.delete()

    def test_alerta_limite_negativo(self):
        conta = Conta.objects.create(
            nome="Banco Limite",
            tipo=Conta.Tipo.BANCO,
            saldo_atual=Decimal("100.00"),
            limite_negativo=Decimal("500.00"),
        )
        self.assertTrue(conta.limite_negativo_ultrapassado(Decimal("-550.00")))
        self.assertTrue(conta.limite_negativo_proximo(Decimal("-470.00")))
