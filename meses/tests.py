from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from contas.models import Conta
from lancamentos.models import Lancamento
from meses.models import SaldoMensalConta
from meses.services import (
    ajustar_saldo_inicial,
    criar_mes,
    elegivel_para_transferencia,
    excluir_serie_futura,
    saldo_do_mes,
    saldos_do_mes,
    atualizar_serie_futura,
    transferir_pendente_para_mes,
)


def _mes_atual():
    hoje = timezone.localdate()
    return hoje.year, hoje.month


def _mes_seguinte(ano, mes):
    if mes == 12:
        return ano + 1, 1
    return ano, mes + 1


class SaldosDoMesTests(TestCase):
    def setUp(self):
        self.ano, self.mes = _mes_atual()
        criar_mes(self.ano, self.mes)
        self.banco = Conta.objects.create(
            nome="Banco Batch",
            tipo=Conta.Tipo.BANCO,
            saldo_atual=Decimal("500.00"),
        )
        self.cartao = Conta.objects.create(nome="Cartao Batch", tipo=Conta.Tipo.CARTAO)

    def _lancar(self, conta, tipo, valor, data_pagamento=None):
        return Lancamento.objects.create(
            descricao=f"{tipo} {valor}",
            tipo=tipo,
            data_vencimento=date(self.ano, self.mes, 10),
            data_pagamento=data_pagamento,
            valor=valor,
            conta=conta,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )

    def test_batch_multiplas_contas_com_fallback(self):
        # Contas criadas apos criar_mes: sem SaldoMensalConta, fallback em saldo_atual
        self._lancar(self.banco, Lancamento.Tipo.RECEBIMENTO_FIXO, Decimal("300.00"))
        self._lancar(self.banco, Lancamento.Tipo.GASTO_FIXO, Decimal("100.00"))
        self._lancar(self.cartao, Lancamento.Tipo.GASTO_VARIAVEL, Decimal("40.00"))

        saldos = saldos_do_mes([self.banco, self.cartao], self.ano, self.mes)

        self.assertEqual(saldos[self.banco.pk].inicial, Decimal("500.00"))
        self.assertEqual(saldos[self.banco.pk].final, Decimal("700.00"))
        self.assertEqual(saldos[self.cartao.pk].inicial, Decimal("0.00"))
        self.assertEqual(saldos[self.cartao.pk].final, Decimal("-40.00"))

    def test_batch_usa_saldo_inicial_registrado(self):
        SaldoMensalConta.objects.create(
            conta=self.banco, ano=self.ano, mes=self.mes, saldo_inicial=Decimal("1000.00")
        )
        saldos = saldos_do_mes([self.banco], self.ano, self.mes)
        self.assertEqual(saldos[self.banco.pk].inicial, Decimal("1000.00"))
        self.assertEqual(saldos[self.banco.pk].final, Decimal("1000.00"))

    def test_batch_respeita_filtro_de_status(self):
        self._lancar(
            self.banco,
            Lancamento.Tipo.RECEBIMENTO_FIXO,
            Decimal("300.00"),
            data_pagamento=date(self.ano, self.mes, 5),
        )
        self._lancar(self.banco, Lancamento.Tipo.GASTO_FIXO, Decimal("100.00"))

        saldos = saldos_do_mes([self.banco], self.ano, self.mes, status_incluidos=["PAGO"])
        self.assertEqual(saldos[self.banco.pk].final, Decimal("800.00"))

    def test_batch_concorda_com_wrapper_escalar(self):
        self._lancar(self.banco, Lancamento.Tipo.RECEBIMENTO_FIXO, Decimal("300.00"))
        self._lancar(self.cartao, Lancamento.Tipo.GASTO_VARIAVEL, Decimal("40.00"))

        saldos = saldos_do_mes([self.banco, self.cartao], self.ano, self.mes)
        for conta in (self.banco, self.cartao):
            self.assertEqual(saldos[conta.pk].final, saldo_do_mes(conta, self.ano, self.mes))

    def test_batch_numero_de_consultas_constante(self):
        self._lancar(self.banco, Lancamento.Tipo.RECEBIMENTO_FIXO, Decimal("300.00"))
        self._lancar(self.cartao, Lancamento.Tipo.GASTO_VARIAVEL, Decimal("40.00"))

        with self.assertNumQueries(2):
            saldos_do_mes([self.banco, self.cartao], self.ano, self.mes)


class MesesServicesTests(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(
            nome="Banco Principal",
            tipo=Conta.Tipo.BANCO,
            saldo_atual=Decimal("1000.00"),
            limite_negativo=Decimal("200.00"),
        )

    def test_criar_primeiro_mes_sem_lancamentos_herda_saldo(self):
        """Task 5.5: Usa mes atual como base, herda saldo da conta."""
        ano, mes = _mes_atual()
        mes_aberto, criados, pendentes, _ = criar_mes(ano, mes)
        self.assertEqual(str(mes_aberto), f"{mes:02d}/{ano}")
        self.assertEqual(len(criados), 0)
        self.assertEqual(pendentes.count(), 0)
        saldo = SaldoMensalConta.objects.get(conta=self.conta, ano=ano, mes=mes)
        self.assertEqual(saldo.saldo_inicial, Decimal("1000.00"))

    def test_propaga_lancamentos_recorrentes_e_nao_propaga_parcela(self):
        """Task 5.5: RECEBIMENTO_FIXO propagado; PARCELA_CARTAO nao propagado."""
        ano, mes = _mes_atual()
        ano2, mes2 = _mes_seguinte(ano, mes)
        criar_mes(ano, mes)
        Lancamento.objects.create(
            descricao="Salario",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(ano, mes, 5),
            valor=Decimal("500.00"),
            conta=self.conta,
            competencia_ano=ano,
            competencia_mes=mes,
        )
        cartao = Conta.objects.create(nome="Cartao A", tipo=Conta.Tipo.CARTAO, dia_vencimento=10)
        Lancamento.objects.create(
            descricao="Notebook 1/10",
            tipo=Lancamento.Tipo.PARCELA_CARTAO,
            data_vencimento=date(ano, mes, 10),
            valor=Decimal("100.00"),
            conta=cartao,
            competencia_ano=ano,
            competencia_mes=mes,
            total_parcelas=10,
            parcela_atual=1,
            gerado_automaticamente=True,
        )

        _, criados, _, _ = criar_mes(ano2, mes2)
        tipos = {item.tipo for item in criados}
        self.assertIn(Lancamento.Tipo.RECEBIMENTO_FIXO, tipos)
        self.assertNotIn(Lancamento.Tipo.PARCELA_CARTAO, tipos)

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
        """Task 5.5: Usa mes atual como base para saldo e conciliacao."""
        ano, mes = _mes_atual()
        criar_mes(ano, mes)
        Lancamento.objects.create(
            descricao="Entrada",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(ano, mes, 10),
            valor=Decimal("80.00"),
            conta=self.conta,
            competencia_ano=ano,
            competencia_mes=mes,
        )
        Lancamento.objects.create(
            descricao="Saida",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=date(ano, mes, 10),
            valor=Decimal("40.00"),
            conta=self.conta,
            competencia_ano=ano,
            competencia_mes=mes,
        )

        self.assertEqual(saldo_do_mes(self.conta, ano, mes), Decimal("1040.00"))
        _, conciliacao = ajustar_saldo_inicial(self.conta, ano, mes, Decimal("980.00"))
        self.assertIsNotNone(conciliacao)
        self.assertEqual(conciliacao.tipo, Lancamento.Tipo.CONCILIACAO)

    def test_pendente_do_mes_anterior(self):
        """Task 5.5: Usa cadeia de meses relativa ao mes atual."""
        ano, mes = _mes_atual()
        ano2, mes2 = _mes_seguinte(ano, mes)
        criar_mes(ano, mes)
        Lancamento.objects.create(
            descricao="Conta atrasada",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=timezone.localdate() - timedelta(days=3),
            valor=Decimal("50.00"),
            conta=self.conta,
            competencia_ano=ano,
            competencia_mes=mes,
        )

        _, _, pendentes, _ = criar_mes(ano2, mes2)
        self.assertEqual(pendentes.count(), 1)

    def test_elegivel_para_transferencia_aceita_pendente_do_mes_anterior(self):
        """Task 5.5: Usa cadeia de meses relativa ao mes atual."""
        ano, mes = _mes_atual()
        ano2, mes2 = _mes_seguinte(ano, mes)
        criar_mes(ano, mes)
        pendente = Lancamento.objects.create(
            descricao="Conta atrasada",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=timezone.localdate() - timedelta(days=3),
            valor=Decimal("50.00"),
            conta=self.conta,
            competencia_ano=ano,
            competencia_mes=mes,
        )
        self.assertTrue(elegivel_para_transferencia(pendente, ano2, mes2))

    def test_elegivel_para_transferencia_rejeita_mes_nao_imediatamente_anterior(self):
        pendente = Lancamento.objects.create(
            descricao="Conta antiga",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=timezone.localdate() - timedelta(days=3),
            valor=Decimal("50.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=2,
        )
        self.assertFalse(elegivel_para_transferencia(pendente, 2026, 5))

    def test_elegivel_para_transferencia_rejeita_lancamento_nao_pendente(self):
        previsto = Lancamento.objects.create(
            descricao="Conta futura",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=timezone.localdate() + timedelta(days=3),
            valor=Decimal("50.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=4,
        )
        self.assertFalse(elegivel_para_transferencia(previsto, 2026, 5))

    def test_transferir_pendente_nao_elegivel_levanta_erro(self):
        nao_elegivel = Lancamento.objects.create(
            descricao="Conta antiga",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=timezone.localdate() - timedelta(days=3),
            valor=Decimal("50.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=2,
        )
        with self.assertRaises(ValidationError):
            transferir_pendente_para_mes(nao_elegivel, 2026, 5)

    # --- Novos testes para regras de sequencia (tasks 5.1, 5.2, 5.3) ---

    def test_primeiro_mes_deve_ser_o_atual(self):
        """Task 5.1: O primeiro mes aberto deve ser o mes atual."""
        hoje = date.today()
        # Escolher um mes diferente do atual
        ano_outro = hoje.year
        mes_outro = hoje.month - 1 if hoje.month > 1 else 12
        if mes_outro == 12 and hoje.month == 1:
            ano_outro -= 1

        with self.assertRaises(ValidationError) as ctx:
            criar_mes(ano_outro, mes_outro)
        self.assertIn(f"{hoje.month:02d}/{hoje.year}", str(ctx.exception))

    def test_nao_pode_pular_mes(self):
        """Task 5.2: Nao e permitido pular meses apos o primeiro."""
        ano, mes = _mes_atual()
        ano2, mes2 = _mes_seguinte(ano, mes)
        ano3, mes3 = _mes_seguinte(ano2, mes2)
        criar_mes(ano, mes)
        with self.assertRaises(ValidationError) as ctx:
            criar_mes(ano3, mes3)
        self.assertIn(f"{mes2:02d}/{ano2}", str(ctx.exception))

    def test_mes_imediatamente_seguinte_e_valido(self):
        """Task 5.2: O mes imediatamente seguinte ao ultimo pode ser criado."""
        ano, mes = _mes_atual()
        ano2, mes2 = _mes_seguinte(ano, mes)
        criar_mes(ano, mes)
        mes_aberto, _, _, _ = criar_mes(ano2, mes2)
        self.assertEqual(str(mes_aberto), f"{mes2:02d}/{ano2}")

    def test_abertura_de_mes_nao_cria_parcelas_duplicadas(self):
        """Task 5.3: Abrir mes nao gera parcelas de cartao ja criadas pela compra."""
        ano, mes = _mes_atual()
        ano2, mes2 = _mes_seguinte(ano, mes)
        criar_mes(ano, mes)
        cartao = Conta.objects.create(nome="Cartao Reg", tipo=Conta.Tipo.CARTAO, dia_vencimento=10)
        # Simula parcelas ja criadas pelo fluxo de compra para mes2
        Lancamento.objects.create(
            descricao="Notebook 1/3",
            tipo=Lancamento.Tipo.PARCELA_CARTAO,
            data_vencimento=date(ano, mes, 10),
            valor=Decimal("100.00"),
            conta=cartao,
            competencia_ano=ano,
            competencia_mes=mes,
            total_parcelas=3,
            parcela_atual=1,
            gerado_automaticamente=True,
        )
        Lancamento.objects.create(
            descricao="Notebook 2/3",
            tipo=Lancamento.Tipo.PARCELA_CARTAO,
            data_vencimento=date(ano2, mes2, 10),
            valor=Decimal("100.00"),
            conta=cartao,
            competencia_ano=ano2,
            competencia_mes=mes2,
            total_parcelas=3,
            parcela_atual=2,
            gerado_automaticamente=True,
        )
        quantidade_antes = Lancamento.objects.filter(
            tipo=Lancamento.Tipo.PARCELA_CARTAO,
            competencia_ano=ano2,
            competencia_mes=mes2,
        ).count()
        criar_mes(ano2, mes2)
        quantidade_depois = Lancamento.objects.filter(
            tipo=Lancamento.Tipo.PARCELA_CARTAO,
            competencia_ano=ano2,
            competencia_mes=mes2,
        ).count()
        self.assertEqual(quantidade_depois, quantidade_antes)

    def test_criar_mes_idempotente_para_mes_ja_aberto(self):
        """Task 1.3: Criar mes para um mes ja aberto e idempotente."""
        ano, mes = _mes_atual()
        criar_mes(ano, mes)
        # Segunda chamada nao deve levantar erro
        mes_aberto, criados, _, _ = criar_mes(ano, mes)
        self.assertEqual(str(mes_aberto), f"{mes:02d}/{ano}")
        self.assertEqual(len(criados), 0)
