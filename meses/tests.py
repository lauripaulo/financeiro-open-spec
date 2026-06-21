from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from contas.models import Conta
from lancamentos.models import Lancamento
from meses.models import SaldoMensalConta
from meses.services import ajustar_saldo_inicial, criar_mes, excluir_serie_futura, saldo_do_mes, atualizar_serie_futura


class MesesServicesTests(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(
            nome="Banco Principal",
            tipo=Conta.Tipo.BANCO,
            saldo_atual=Decimal("1000.00"),
            limite_negativo=Decimal("200.00"),
        )

    def test_criar_primeiro_mes_sem_lancamentos_herda_saldo(self):
        mes_aberto, criados, pendentes, _ = criar_mes(2026, 4)
        self.assertEqual(str(mes_aberto), "04/2026")
        self.assertEqual(len(criados), 0)
        self.assertEqual(pendentes.count(), 0)
        saldo = SaldoMensalConta.objects.get(conta=self.conta, ano=2026, mes=4)
        self.assertEqual(saldo.saldo_inicial, Decimal("1000.00"))

    def test_propaga_lancamentos_recorrentes_e_parcela(self):
        criar_mes(2026, 4)
        Lancamento.objects.create(
            descricao="Salario",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(2026, 4, 5),
            valor=Decimal("500.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=4,
        )
        parcela = Lancamento.objects.create(
            descricao="Notebook 1/10",
            tipo=Lancamento.Tipo.PARCELA_CARTAO,
            data_vencimento=date(2026, 4, 10),
            valor=Decimal("100.00"),
            conta=Conta.objects.create(nome="Cartao A", tipo=Conta.Tipo.CARTAO, dia_vencimento=10),
            competencia_ano=2026,
            competencia_mes=4,
            total_parcelas=10,
            parcela_atual=1,
            gerado_automaticamente=True,
        )

        _, criados, _, _ = criar_mes(2026, 5)
        tipos = {item.tipo for item in criados}
        self.assertIn(Lancamento.Tipo.RECEBIMENTO_FIXO, tipos)
        self.assertIn(Lancamento.Tipo.PARCELA_CARTAO, tipos)
        nova_parcela = Lancamento.objects.get(grupo_recorrencia=parcela.grupo_recorrencia, competencia_ano=2026, competencia_mes=5)
        self.assertEqual(nova_parcela.parcela_atual, 2)

    def test_edicao_recorrente_sobrescreve_instancias_futuras(self):
        origem = Lancamento.objects.create(
            descricao="Internet",
            tipo=Lancamento.Tipo.ASSINATURA,
            data_vencimento=date(2026, 4, 10),
            valor=Decimal("80.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=4,
        )
        futuro = Lancamento.objects.create(
            descricao="Internet",
            tipo=Lancamento.Tipo.ASSINATURA,
            data_vencimento=date(2026, 5, 10),
            valor=Decimal("120.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=5,
            grupo_recorrencia=origem,
            gerado_automaticamente=True,
        )

        atualizar_serie_futura(origem, valor=Decimal("100.00"))
        futuro.refresh_from_db()
        self.assertEqual(futuro.valor, Decimal("100.00"))

    def test_exclusao_recorrente_remove_futuros(self):
        origem = Lancamento.objects.create(
            descricao="Streaming",
            tipo=Lancamento.Tipo.ASSINATURA,
            data_vencimento=date(2026, 4, 10),
            valor=Decimal("40.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=4,
        )
        Lancamento.objects.create(
            descricao="Streaming",
            tipo=Lancamento.Tipo.ASSINATURA,
            data_vencimento=date(2026, 5, 10),
            valor=Decimal("40.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=5,
            grupo_recorrencia=origem,
            gerado_automaticamente=True,
        )

        excluir_serie_futura(origem)
        self.assertFalse(Lancamento.objects.filter(descricao="Streaming").exists())

    def test_saldo_e_conciliacao(self):
        criar_mes(2026, 4)
        Lancamento.objects.create(
            descricao="Entrada",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(2026, 4, 10),
            valor=Decimal("80.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=4,
        )
        Lancamento.objects.create(
            descricao="Saida",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=date(2026, 4, 10),
            valor=Decimal("40.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=4,
        )

        self.assertEqual(saldo_do_mes(self.conta, 2026, 4), Decimal("1040.00"))
        _, conciliacao = ajustar_saldo_inicial(self.conta, 2026, 4, Decimal("980.00"))
        self.assertIsNotNone(conciliacao)
        self.assertEqual(conciliacao.tipo, Lancamento.Tipo.CONCILIACAO)

    def test_pendente_do_mes_anterior(self):
        criar_mes(2026, 4)
        Lancamento.objects.create(
            descricao="Conta atrasada",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=date.today() - timedelta(days=3),
            valor=Decimal("50.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=4,
        )

        _, _, pendentes, _ = criar_mes(2026, 5)
        self.assertEqual(pendentes.count(), 1)
