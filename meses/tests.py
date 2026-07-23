from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from contas.models import Conta
from lancamentos.models import Lancamento
from meses.models import MesAberto, SaldoMensalConta
from meses.services import (
    _mes_anterior,
    _mes_posterior,
    _saldo_inicial_do_mes,
    _mes_referencia_seguro,
    ajustar_saldo_inicial,
    criar_mes,
    elegivel_para_transferencia,
    excluir_serie_futura,
    saldo_do_mes,
    saldo_investimento,
    saldo_projetado_em_data,
    saldo_real_em_data,
    saldos_do_mes,
    atualizar_serie_futura,
    total_gastos_cartao_por_mes,
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
        # Escolher um mes diferente do atual (sem branch condicional)
        mes_decimal = hoje.year * 12 + hoje.month - 1
        ano_outro, mes_outro = divmod(mes_decimal - 1, 12)
        mes_outro += 1

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

    def test_atualizar_serie_nao_recorrente(self):
        ano, mes = _mes_atual()
        criar_mes(ano, mes)
        lanc = Lancamento.objects.create(
            descricao="Pontual",
            tipo=Lancamento.Tipo.GASTO_VARIAVEL,
            data_vencimento=timezone.localdate(),
            valor=Decimal("10.00"),
            conta=self.conta,
            competencia_ano=ano,
            competencia_mes=mes,
        )
        atualizar_serie_futura(lanc, valor=Decimal("20.00"))
        lanc.refresh_from_db()
        self.assertEqual(lanc.valor, Decimal("20.00"))

    def test_excluir_serie_nao_recorrente(self):
        ano, mes = _mes_atual()
        criar_mes(ano, mes)
        lanc = Lancamento.objects.create(
            descricao="Pontual",
            tipo=Lancamento.Tipo.GASTO_VARIAVEL,
            data_vencimento=timezone.localdate(),
            valor=Decimal("10.00"),
            conta=self.conta,
            competencia_ano=ano,
            competencia_mes=mes,
        )
        pk = lanc.pk
        excluir_serie_futura(lanc)
        self.assertFalse(Lancamento.objects.filter(pk=pk).exists())

    def test_ajustar_saldo_sem_mudanca(self):
        ano, mes = _mes_atual()
        criar_mes(ano, mes)
        registro, conciliacao = ajustar_saldo_inicial(self.conta, ano, mes, Decimal("1000.00"))
        self.assertIsNone(conciliacao)

    def test_saldo_investimento_conta_nao_investimento(self):
        from meses.services import saldo_investimento
        self.assertEqual(saldo_investimento(self.conta), Decimal("0.00"))


    def test_atualizar_serie_nao_propaga_para_meses_anteriores(self):
        """Se edita uma ocorrencia futura, meses anteriores ao editado nao mudam."""
        raiz = Lancamento.objects.create(
            descricao="Internet",
            tipo=Lancamento.Tipo.ASSINATURA,
            data_vencimento=date(2026, 4, 10),
            valor=Decimal("80.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=4,
        )
        anterior = Lancamento.objects.create(
            descricao="Internet",
            tipo=Lancamento.Tipo.ASSINATURA,
            data_vencimento=date(2026, 5, 10),
            valor=Decimal("80.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=5,
            grupo_recorrencia=raiz,
            gerado_automaticamente=True,
        )
        futuro = Lancamento.objects.create(
            descricao="Internet",
            tipo=Lancamento.Tipo.ASSINATURA,
            data_vencimento=date(2026, 6, 10),
            valor=Decimal("80.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=6,
            grupo_recorrencia=raiz,
            gerado_automaticamente=True,
        )

        atualizar_serie_futura(futuro, valor=Decimal("100.00"))
        anterior.refresh_from_db()
        futuro.refresh_from_db()
        self.assertEqual(anterior.valor, Decimal("80.00"))
        self.assertEqual(futuro.valor, Decimal("100.00"))

    def test_saldo_investimento_ate_competencia(self):
        invest = Conta.objects.create(
            nome="Invest SI", tipo=Conta.Tipo.INVESTIMENTO, saldo_atual=Decimal("1000.00")
        )
        Lancamento.objects.create(
            descricao="Aporte passado",
            tipo=Lancamento.Tipo.APORTE,
            data_vencimento=date(2026, 4, 10),
            valor=Decimal("200.00"),
            conta=invest,
            competencia_ano=2026,
            competencia_mes=4,
        )
        Lancamento.objects.create(
            descricao="Aporte futuro",
            tipo=Lancamento.Tipo.APORTE,
            data_vencimento=date(2026, 6, 10),
            valor=Decimal("300.00"),
            conta=invest,
            competencia_ano=2026,
            competencia_mes=6,
        )
        self.assertEqual(saldo_investimento(invest, ate_ano=2026, ate_mes=5), Decimal("1200.00"))


class MesModelsTests(TestCase):
    def test_mes_aberto_str(self):
        mes = MesAberto(ano=2025, mes=3)
        self.assertEqual(str(mes), "03/2025")

    def test_mes_aberto_mes_invalido(self):
        mes = MesAberto(ano=2025, mes=13)
        with self.assertRaises(ValidationError) as ctx:
            mes.full_clean()
        self.assertIn("mes", ctx.exception.message_dict)

    def test_saldo_mensal_conta_str(self):
        conta = Conta.objects.create(nome="Banco", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("0.00"))
        smc = SaldoMensalConta(conta=conta, ano=2025, mes=3)
        self.assertEqual(str(smc), f"{conta} - 03/2025")

    def test_saldo_mensal_conta_mes_invalido(self):
        conta = Conta.objects.create(nome="Banco", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("0.00"))
        smc = SaldoMensalConta(conta=conta, ano=2025, mes=13)
        with self.assertRaises(ValidationError) as ctx:
            smc.full_clean()
        self.assertIn("mes", ctx.exception.message_dict)

    def test_data_mes_segura_ultimo_dia(self):
        from meses.services import _data_mes_segura
        self.assertEqual(_data_mes_segura(2025, 2, 31), date(2025, 2, 28))

    def test_mes_anterior_ano_novo(self):
        self.assertEqual(_mes_anterior(2026, 1), (2025, 12))

    def test_mes_posterior_dezembro(self):
        self.assertEqual(_mes_posterior(2026, 12), (2027, 1))

    def test_saldo_inicial_do_mes_com_registro(self):
        conta = Conta.objects.create(nome="Banco SMC", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("0.00"))
        ano, mes = _mes_atual()
        criar_mes(ano, mes)
        registro = SaldoMensalConta.objects.get(conta=conta, ano=ano, mes=mes)
        registro.saldo_inicial = Decimal("1234.00")
        registro.save()
        self.assertEqual(_saldo_inicial_do_mes(conta, ano, mes), Decimal("1234.00"))

    def test_mes_referencia_seguro_sem_meses_abertos(self):
        MesAberto.objects.all().delete()
        d = date(2026, 3, 15)
        self.assertEqual(_mes_referencia_seguro(d), (2026, 3))


class MesesViewsTests(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(
            nome="Banco MV", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("0.00")
        )
        self.ano, self.mes = _mes_atual()
        criar_mes(self.ano, self.mes)

    def test_criar_mes_view_com_aviso_limite_meses(self):
        from unittest.mock import patch
        url = reverse("visualizacao:criar_mes")
        with patch("visualizacao.views._carregar_mes", return_value=(None, Lancamento.objects.none(), True)):
            response = self.client.post(url, {"ano": str(self.ano), "mes": str(self.mes)})
        self.assertEqual(response.status_code, 302)

    def test_criar_mes_view_com_pendentes(self):
        hoje = date.today()
        Lancamento.objects.create(
            descricao="Atrasada",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=hoje - timedelta(days=3),
            valor=Decimal("10.00"),
            conta=self.conta,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )
        ano2, mes2 = _mes_seguinte(self.ano, self.mes)
        url = reverse("visualizacao:criar_mes")
        response = self.client.post(url, {"ano": str(ano2), "mes": str(mes2)})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("visualizacao:resolver_pendentes_abertura"), response.url)

    def test_resolver_pendentes_redireciona_quando_vazio(self):
        ano2, mes2 = _mes_seguinte(self.ano, self.mes)
        criar_mes(ano2, mes2)
        url = reverse("visualizacao:resolver_pendentes_abertura")
        response = self.client.get(url, {"ano": str(ano2), "mes": str(mes2)})
        self.assertEqual(response.status_code, 302)


class SaldoRealEmDataTests(TestCase):
    def setUp(self):
        self.ano, self.mes = _mes_atual()
        criar_mes(self.ano, self.mes)
        self.conta = Conta.objects.create(
            nome="Banco Teste",
            tipo=Conta.Tipo.BANCO,
            saldo_atual=Decimal("1000.00"),
        )
        SaldoMensalConta.objects.filter(conta=self.conta, ano=self.ano, mes=self.mes).update(
            saldo_inicial=Decimal("1000.00")
        )
        self.hoje = date(self.ano, self.mes, 15)

    def _lancar(self, tipo, valor, data_pagamento=None, dia_vencimento=10):
        return Lancamento.objects.create(
            descricao=f"L {tipo}",
            tipo=tipo,
            data_vencimento=date(self.ano, self.mes, dia_vencimento),
            data_pagamento=data_pagamento,
            valor=valor,
            conta=self.conta,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )

    def test_sem_lancamentos_retorna_saldo_inicial(self):
        resultado = saldo_real_em_data(self.conta, self.hoje)
        self.assertEqual(resultado, Decimal("1000.00"))

    def test_inclui_apenas_pagos_ate_data(self):
        self._lancar(Lancamento.Tipo.RECEBIMENTO_EXCEPCIONAL, Decimal("500.00"), data_pagamento=self.hoje)
        self._lancar(Lancamento.Tipo.GASTO_VARIAVEL, Decimal("200.00"))  # sem data_pagamento
        resultado = saldo_real_em_data(self.conta, self.hoje)
        self.assertEqual(resultado, Decimal("1500.00"))

    def test_exclui_pagos_apos_data(self):
        amanha = self.hoje + timedelta(days=1)
        self._lancar(Lancamento.Tipo.RECEBIMENTO_EXCEPCIONAL, Decimal("500.00"), data_pagamento=amanha)
        resultado = saldo_real_em_data(self.conta, self.hoje)
        self.assertEqual(resultado, Decimal("1000.00"))

    def test_fallback_sem_saldo_mensal_conta(self):
        SaldoMensalConta.objects.filter(conta=self.conta).delete()
        resultado = saldo_real_em_data(self.conta, self.hoje)
        self.assertEqual(resultado, Decimal("1000.00"))

    def test_entrada_aumenta_saldo(self):
        self._lancar(Lancamento.Tipo.RECEBIMENTO_FIXO, Decimal("3000.00"), data_pagamento=self.hoje)
        resultado = saldo_real_em_data(self.conta, self.hoje)
        self.assertEqual(resultado, Decimal("4000.00"))

    def test_saida_diminui_saldo(self):
        self._lancar(Lancamento.Tipo.GASTO_FIXO, Decimal("300.00"), data_pagamento=self.hoje)
        resultado = saldo_real_em_data(self.conta, self.hoje)
        self.assertEqual(resultado, Decimal("700.00"))


class SaldoProjetadoEmDataTests(TestCase):
    def setUp(self):
        self.ano, self.mes = _mes_atual()
        criar_mes(self.ano, self.mes)
        self.conta = Conta.objects.create(
            nome="Banco Projetado",
            tipo=Conta.Tipo.BANCO,
            saldo_atual=Decimal("1000.00"),
        )
        SaldoMensalConta.objects.filter(conta=self.conta, ano=self.ano, mes=self.mes).update(
            saldo_inicial=Decimal("1000.00")
        )
        self.hoje = date(self.ano, self.mes, 15)

    def _lancar(self, tipo, valor, data_pagamento=None, dia_vencimento=10):
        return Lancamento.objects.create(
            descricao=f"L {tipo}",
            tipo=tipo,
            data_vencimento=date(self.ano, self.mes, dia_vencimento),
            data_pagamento=data_pagamento,
            valor=valor,
            conta=self.conta,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )

    def test_inclui_pagos_e_previstos_ate_data(self):
        self._lancar(Lancamento.Tipo.RECEBIMENTO_FIXO, Decimal("3000.00"), data_pagamento=self.hoje)
        self._lancar(Lancamento.Tipo.GASTO_VARIAVEL, Decimal("500.00"), dia_vencimento=15)
        resultado = saldo_projetado_em_data(self.conta, self.hoje)
        self.assertEqual(resultado, Decimal("3500.00"))

    def test_exclui_previstos_apos_data(self):
        self._lancar(Lancamento.Tipo.GASTO_VARIAVEL, Decimal("500.00"), dia_vencimento=20)
        resultado = saldo_projetado_em_data(self.conta, self.hoje)
        self.assertEqual(resultado, Decimal("1000.00"))

    def test_projetado_com_saida_menor_que_real(self):
        self._lancar(Lancamento.Tipo.RECEBIMENTO_FIXO, Decimal("3000.00"),
                     data_pagamento=self.hoje - timedelta(days=1))
        self._lancar(Lancamento.Tipo.GASTO_VARIAVEL, Decimal("100.00"), dia_vencimento=15)
        real = saldo_real_em_data(self.conta, self.hoje)
        projetado = saldo_projetado_em_data(self.conta, self.hoje)
        self.assertLessEqual(projetado, real)

    def test_sem_lancamentos_retorna_saldo_inicial(self):
        resultado = saldo_projetado_em_data(self.conta, self.hoje)
        self.assertEqual(resultado, Decimal("1000.00"))


class TotalGastosCartaoPorMesTests(TestCase):
    def setUp(self):
        self.ano, self.mes = _mes_atual()
        criar_mes(self.ano, self.mes)
        self.cartao = Conta.objects.create(nome="Visa Teste", tipo=Conta.Tipo.CARTAO)

    def _lancar_cartao(self, tipo, valor, ano=None, mes=None, data_pagamento=None):
        a = ano or self.ano
        m = mes or self.mes
        return Lancamento.objects.create(
            descricao=f"Compra {valor}",
            tipo=tipo,
            data_vencimento=date(a, m, 10),
            data_pagamento=data_pagamento,
            valor=valor,
            conta=self.cartao,
            competencia_ano=a,
            competencia_mes=m,
        )

    def test_mes_atual_soma_saidas(self):
        self._lancar_cartao(Lancamento.Tipo.GASTO_VARIAVEL, Decimal("100.00"))
        self._lancar_cartao(Lancamento.Tipo.ASSINATURA, Decimal("50.00"))
        resultado = total_gastos_cartao_por_mes([self.cartao])
        chave = (self.ano, self.mes)
        self.assertIn(chave, resultado)
        self.assertEqual(resultado[chave][self.cartao.pk], Decimal("150.00"))

    def test_inclui_pagos_e_nao_pagos(self):
        self._lancar_cartao(Lancamento.Tipo.GASTO_VARIAVEL, Decimal("200.00"),
                            data_pagamento=date(self.ano, self.mes, 5))
        self._lancar_cartao(Lancamento.Tipo.GASTO_VARIAVEL, Decimal("300.00"))
        resultado = total_gastos_cartao_por_mes([self.cartao])
        chave = (self.ano, self.mes)
        self.assertEqual(resultado[chave][self.cartao.pk], Decimal("500.00"))

    def test_maximo_quatro_meses(self):
        a, m = _mes_seguinte(self.ano, self.mes)
        for _ in range(5):
            criar_mes(a, m)
            a, m = _mes_seguinte(a, m)
        resultado = total_gastos_cartao_por_mes([self.cartao])
        self.assertLessEqual(len(resultado), 4)

    def test_sem_meses_abertos_retorna_vazio(self):
        from meses.models import MesAberto
        MesAberto.objects.all().delete()
        resultado = total_gastos_cartao_por_mes([self.cartao])
        self.assertEqual(resultado, {})
