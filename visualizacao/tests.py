from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from contas.models import Conta
from lancamentos.models import Lancamento
from meses.services import criar_mes, saldo_do_mes, transferir_pendente_para_mes
from visualizacao.services import resumo_consolidado
from visualizacao.templatetags.moeda import moeda
from visualizacao.views import _filtros_mes


def _mes_atual():
    hoje = timezone.localdate()
    return hoje.year, hoje.month


def _mes_seguinte(ano, mes):
    if mes == 12:
        return ano + 1, 1
    return ano, mes + 1


class MoedaFilterTests(TestCase):
    def test_valor_simples(self):
        self.assertEqual(moeda(Decimal("256432.11")), "R$ 256.432,11")

    def test_valor_sem_decimais(self):
        self.assertEqual(moeda(Decimal("100")), "R$ 100,00")

    def test_valor_pequeno(self):
        self.assertEqual(moeda(Decimal("9.5")), "R$ 9,50")

    def test_none_retorna_zero(self):
        self.assertEqual(moeda(None), "R$ 0,00")

    def test_string_vazia_retorna_zero(self):
        self.assertEqual(moeda(""), "R$ 0,00")

    def test_valor_negativo(self):
        self.assertEqual(moeda(Decimal("-1234.56")), "-R$ 1.234,56")

    def test_valor_milhoes(self):
        self.assertEqual(moeda(Decimal("1234567.89")), "R$ 1.234.567,89")

    def test_valor_invalido_retorna_vazio(self):
        self.assertEqual(moeda("abc"), "")


class FiltrosMesTests(TestCase):
    def _get_request(self, params=None):
        return self.client.get("/", params or {}).wsgi_request

    def test_retorna_ano_e_mes_do_get(self):
        request = self.client.get("/", {"ano": "2025", "mes": "3"}).wsgi_request
        ano, mes = _filtros_mes(request)
        self.assertEqual(ano, 2025)
        self.assertEqual(mes, 3)

    def test_parametros_invalidos_retornam_hoje(self):
        request = self.client.get("/", {"ano": "abc", "mes": "xyz"}).wsgi_request
        ano, mes = _filtros_mes(request)
        hoje = date.today()
        self.assertEqual(ano, hoje.year)
        self.assertEqual(mes, hoje.month)

    def test_mes_fora_do_intervalo_retorna_hoje(self):
        request = self.client.get("/", {"ano": "2025", "mes": "13"}).wsgi_request
        ano, mes = _filtros_mes(request)
        hoje = date.today()
        self.assertEqual(ano, hoje.year)
        self.assertEqual(mes, hoje.month)

    def test_mes_zero_retorna_hoje(self):
        request = self.client.get("/", {"ano": "2025", "mes": "0"}).wsgi_request
        ano, mes = _filtros_mes(request)
        hoje = date.today()
        self.assertEqual(ano, hoje.year)
        self.assertEqual(mes, hoje.month)

    def test_post_tem_prioridade_sobre_get(self):
        request = self.client.post("/?ano=2020&mes=1", {"ano": "2025", "mes": "6"}).wsgi_request
        ano, mes = _filtros_mes(request)
        self.assertEqual(ano, 2025)
        self.assertEqual(mes, 6)


class ResumoConsolidadoServiceTests(TestCase):
    def setUp(self):
        self.banco = Conta.objects.create(
            nome="Banco A",
            tipo=Conta.Tipo.BANCO,
            saldo_atual=Decimal("500.00"),
        )
        self.cartao = Conta.objects.create(nome="Cartao B", tipo=Conta.Tipo.CARTAO)
        self.ano, self.mes = _mes_atual()
        criar_mes(self.ano, self.mes)

    def _lancar(self, conta, tipo, valor, dia=10, data_pagamento=None):
        return Lancamento.objects.create(
            descricao=f"{tipo} {valor}",
            tipo=tipo,
            data_vencimento=date(self.ano, self.mes, dia),
            data_pagamento=data_pagamento,
            valor=valor,
            conta=conta,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )

    def test_resumo_basico_sem_http(self):
        self._lancar(self.banco, Lancamento.Tipo.RECEBIMENTO_FIXO, Decimal("300.00"))
        self._lancar(self.banco, Lancamento.Tipo.GASTO_FIXO, Decimal("100.00"))
        self._lancar(self.cartao, Lancamento.Tipo.GASTO_VARIAVEL, Decimal("40.00"))

        resumo = resumo_consolidado(self.ano, self.mes)

        self.assertEqual(len(resumo.lancamentos), 3)
        self.assertEqual(resumo.total_entradas, Decimal("300.00"))
        self.assertEqual(resumo.total_saidas, Decimal("140.00"))
        # Banco: 500 + 300 - 100 = 700; Cartao: 0 - 40 = -40
        self.assertEqual(resumo.saldo_total, Decimal("660.00"))
        self.assertEqual(len(resumo.contas_ajuste), 2)
        self.assertEqual(resumo.alertas_limite, [])
        self.assertIsNone(resumo.conta_selecionada)

    def test_filtro_por_conta_restringe_lista_totais_e_saldo(self):
        self._lancar(self.banco, Lancamento.Tipo.RECEBIMENTO_FIXO, Decimal("300.00"))
        self._lancar(self.cartao, Lancamento.Tipo.GASTO_VARIAVEL, Decimal("40.00"))

        resumo = resumo_consolidado(self.ano, self.mes, conta_id=self.banco.pk)

        self.assertTrue(all(l.conta_id == self.banco.pk for l in resumo.lancamentos))
        self.assertEqual(resumo.total_entradas, Decimal("300.00"))
        self.assertEqual(resumo.total_saidas, Decimal("0.00"))
        self.assertEqual(resumo.saldo_total, Decimal("800.00"))
        self.assertEqual(resumo.conta_selecionada, self.banco)

    def test_filtro_por_status_restringe_lista_totais_e_saldos(self):
        self._lancar(
            self.banco,
            Lancamento.Tipo.RECEBIMENTO_FIXO,
            Decimal("300.00"),
            data_pagamento=date(self.ano, self.mes, 5),
        )
        self._lancar(self.banco, Lancamento.Tipo.GASTO_FIXO, Decimal("100.00"), dia=28)

        resumo = resumo_consolidado(self.ano, self.mes, status=["PAGO"])

        self.assertEqual(len(resumo.lancamentos), 1)
        self.assertEqual(resumo.total_entradas, Decimal("300.00"))
        self.assertEqual(resumo.total_saidas, Decimal("0.00"))
        self.assertEqual(resumo.saldo_total, Decimal("800.00"))

    def test_conta_investimento_fica_fora_do_resumo(self):
        investimento = Conta.objects.create(
            nome="Tesouro",
            tipo=Conta.Tipo.INVESTIMENTO,
            saldo_atual=Decimal("10000.00"),
        )
        Lancamento.objects.create(
            descricao="Aporte",
            tipo=Lancamento.Tipo.APORTE,
            data_vencimento=date(self.ano, self.mes, 10),
            valor=Decimal("1000.00"),
            conta=investimento,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )

        resumo = resumo_consolidado(self.ano, self.mes)

        self.assertEqual(resumo.lancamentos, [])
        self.assertEqual(resumo.saldo_total, Decimal("500.00"))
        contas = [item["conta"] for item in resumo.contas_ajuste]
        self.assertNotIn(investimento, contas)

    def test_alertas_cobrem_todas_as_contas_banco_mesmo_com_filtro(self):
        estourada = Conta.objects.create(
            nome="Banco Estourado",
            tipo=Conta.Tipo.BANCO,
            saldo_atual=Decimal("0.00"),
            limite_negativo=Decimal("100.00"),
        )
        self._lancar(estourada, Lancamento.Tipo.GASTO_FIXO, Decimal("500.00"))

        resumo = resumo_consolidado(self.ano, self.mes, conta_id=self.banco.pk)

        self.assertIn("Banco Estourado: limite negativo ultrapassado.", resumo.alertas_limite)

    def test_saldos_concordam_com_saldo_do_mes(self):
        self._lancar(self.banco, Lancamento.Tipo.RECEBIMENTO_FIXO, Decimal("300.00"))
        self._lancar(
            self.banco,
            Lancamento.Tipo.GASTO_FIXO,
            Decimal("100.00"),
            data_pagamento=date(self.ano, self.mes, 5),
        )
        self._lancar(self.cartao, Lancamento.Tipo.GASTO_VARIAVEL, Decimal("40.00"))

        for status in (None, ["PAGO"], ["PREVISTO", "PENDENTE"]):
            resumo = resumo_consolidado(self.ano, self.mes, status=status)
            esperado = sum(
                (
                    saldo_do_mes(conta, self.ano, self.mes, status_incluidos=status)
                    for conta in (self.banco, self.cartao)
                ),
                Decimal("0.00"),
            )
            self.assertEqual(resumo.saldo_total, esperado, f"status={status}")

            # cada conta individualmente, nao so por transitividade
            for conta in (self.banco, self.cartao):
                resumo_conta = resumo_consolidado(
                    self.ano, self.mes, conta_id=conta.pk, status=status
                )
                self.assertEqual(
                    resumo_conta.saldo_total,
                    saldo_do_mes(conta, self.ano, self.mes, status_incluidos=status),
                    f"conta={conta.nome} status={status}",
                )

    def test_numero_constante_de_consultas(self):
        self._lancar(self.banco, Lancamento.Tipo.RECEBIMENTO_FIXO, Decimal("300.00"))
        self._lancar(self.cartao, Lancamento.Tipo.GASTO_VARIAVEL, Decimal("40.00"))

        # contas + lancamentos exibidos + as duas de saldos_do_mes
        # (SaldoMensalConta e Lancamento), independente do numero de contas
        with self.assertNumQueries(4):
            resumo_consolidado(self.ano, self.mes)


class VisaoConsolidadaTests(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(
            nome="Banco Teste",
            tipo=Conta.Tipo.BANCO,
            saldo_atual=Decimal("500.00"),
        )
        self.ano, self.mes = _mes_atual()
        criar_mes(self.ano, self.mes)
        self.url = reverse("visualizacao:consolidada")

    def test_mes_nao_criado_renderiza_pagina_especifica(self):
        # Use a far-future month that doesn't exist
        response = self.client.get(self.url, {"ano": "2099", "mes": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "visualizacao/mes_nao_criado.html")

    def test_mes_criado_renderiza_consolidada(self):
        response = self.client.get(self.url, {"ano": str(self.ano), "mes": str(self.mes)})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "visualizacao/consolidada.html")

    def test_filtra_por_conta(self):
        outra = Conta.objects.create(nome="Outro Banco", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("0.00"))
        Lancamento.objects.create(
            descricao="Entrada conta principal",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(self.ano, self.mes, 10),
            valor=Decimal("100.00"),
            conta=self.conta,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )
        Lancamento.objects.create(
            descricao="Entrada outra conta",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(self.ano, self.mes, 10),
            valor=Decimal("200.00"),
            conta=outra,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )
        response = self.client.get(self.url, {"ano": str(self.ano), "mes": str(self.mes), "conta": str(self.conta.pk)})
        self.assertEqual(response.status_code, 200)
        lancamentos = response.context["lancamentos"]
        self.assertTrue(all(l.conta_id == self.conta.pk for l in lancamentos))

    def test_filtra_por_status_pago(self):
        Lancamento.objects.create(
            descricao="Pago",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(self.ano, self.mes, 1),
            data_pagamento=date(self.ano, self.mes, 1),
            valor=Decimal("50.00"),
            conta=self.conta,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )
        Lancamento.objects.create(
            descricao="Nao pago",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(self.ano, self.mes, 28),
            valor=Decimal("50.00"),
            conta=self.conta,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )
        response = self.client.get(self.url, {"ano": str(self.ano), "mes": str(self.mes), "status": "PAGO"})
        self.assertEqual(response.status_code, 200)
        lancamentos = response.context["lancamentos"]
        self.assertTrue(all(l.status == Lancamento.Status.PAGO for l in lancamentos))
        self.assertEqual(len(lancamentos), 1)

    def test_saldo_total_restrito_a_conta_filtrada(self):
        outra = Conta.objects.create(nome="Outro Banco Saldo", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("0.00"))
        Lancamento.objects.create(
            descricao="Entrada conta principal",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(self.ano, self.mes, 10),
            valor=Decimal("100.00"),
            conta=self.conta,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )
        Lancamento.objects.create(
            descricao="Entrada outra conta",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(self.ano, self.mes, 10),
            valor=Decimal("200.00"),
            conta=outra,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )

        response_sem_filtro = self.client.get(self.url, {"ano": str(self.ano), "mes": str(self.mes)})
        response_com_filtro = self.client.get(self.url, {"ano": str(self.ano), "mes": str(self.mes), "conta": str(self.conta.pk)})

        self.assertEqual(response_sem_filtro.context["saldo_total"], Decimal("800.00"))
        self.assertEqual(response_com_filtro.context["saldo_total"], Decimal("600.00"))

    def test_filtro_de_status_gera_lista_e_saldo_coerentes(self):
        Lancamento.objects.create(
            descricao="Pago",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(self.ano, self.mes, 1),
            data_pagamento=date(self.ano, self.mes, 1),
            valor=Decimal("50.00"),
            conta=self.conta,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )
        Lancamento.objects.create(
            descricao="Nao pago",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(self.ano, self.mes, 28),
            valor=Decimal("999.00"),
            conta=self.conta,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )
        response = self.client.get(
            self.url, {"ano": str(self.ano), "mes": str(self.mes), "conta": str(self.conta.pk), "status": "PAGO"}
        )
        self.assertEqual(len(response.context["lancamentos"]), 1)
        self.assertEqual(response.context["saldo_total"], Decimal("550.00"))

    def test_totais_entradas_e_saidas(self):
        Lancamento.objects.create(
            descricao="Salario",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(self.ano, self.mes, 5),
            valor=Decimal("1000.00"),
            conta=self.conta,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )
        Lancamento.objects.create(
            descricao="Aluguel",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=date(self.ano, self.mes, 10),
            valor=Decimal("300.00"),
            conta=self.conta,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )
        response = self.client.get(self.url, {"ano": str(self.ano), "mes": str(self.mes)})
        self.assertEqual(response.context["total_entradas"], Decimal("1000.00"))
        self.assertEqual(response.context["total_saidas"], Decimal("300.00"))

    def test_totais_exibidos_no_padrao_brasileiro(self):
        Lancamento.objects.create(
            descricao="Salario",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(self.ano, self.mes, 5),
            valor=Decimal("1234.56"),
            conta=self.conta,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )
        response = self.client.get(self.url, {"ano": str(self.ano), "mes": str(self.mes)})
        self.assertContains(response, "R$ 1.234,56")


class VisaoPatrimonioTests(TestCase):
    def test_exibe_saldo_no_padrao_brasileiro(self):
        conta = Conta.objects.create(
            nome="Investimento Teste",
            tipo=Conta.Tipo.INVESTIMENTO,
            saldo_atual=Decimal("0.00"),
        )
        Lancamento.objects.create(
            descricao="Aporte",
            tipo=Lancamento.Tipo.APORTE,
            data_vencimento=date(2026, 4, 10),
            valor=Decimal("1234.56"),
            conta=conta,
            competencia_ano=2026,
            competencia_mes=4,
        )
        response = self.client.get(reverse("visualizacao:patrimonio"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "R$ 1.234,56")

    def test_titulo_exibe_total_consolidado_das_contas_investimento(self):
        Conta.objects.create(
            nome="Invest A",
            tipo=Conta.Tipo.INVESTIMENTO,
            saldo_atual=Decimal("100000.00"),
        )
        Conta.objects.create(
            nome="Invest B",
            tipo=Conta.Tipo.INVESTIMENTO,
            saldo_atual=Decimal("80023.23"),
        )

        response = self.client.get(reverse("visualizacao:patrimonio"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visao de patrimonio: Total R$ 180.023,23")

    def test_titulo_exibe_total_zerado_sem_contas_investimento(self):
        response = self.client.get(reverse("visualizacao:patrimonio"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visao de patrimonio: Total R$ 0,00")


class TransferirPendenteTests(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(
            nome="Banco TP",
            tipo=Conta.Tipo.BANCO,
            saldo_atual=Decimal("100.00"),
        )
        self.ano1, self.mes1 = _mes_atual()
        self.ano2, self.mes2 = _mes_seguinte(self.ano1, self.mes1)
        criar_mes(self.ano1, self.mes1)
        criar_mes(self.ano2, self.mes2)
        self.lancamento = Lancamento.objects.create(
            descricao="Conta atrasada",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=timezone.localdate() - timedelta(days=5),
            valor=Decimal("80.00"),
            conta=self.conta,
            competencia_ano=self.ano1,
            competencia_mes=self.mes1,
        )

    def test_transfere_lancamento_para_mes_atual(self):
        url = reverse("visualizacao:transferir_pendente", args=[self.lancamento.pk])
        response = self.client.post(url, {"ano": str(self.ano2), "mes": str(self.mes2)})
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.headers["HX-Refresh"], "true")
        self.lancamento.refresh_from_db()
        self.assertEqual(self.lancamento.competencia_mes, self.mes2)
        self.assertEqual(self.lancamento.competencia_ano, self.ano2)

    def test_retorna_400_para_pk_inexistente(self):
        url = reverse("visualizacao:transferir_pendente", args=[99999])
        response = self.client.post(url, {"ano": str(self.ano2), "mes": str(self.mes2)})
        self.assertEqual(response.status_code, 400)

    def test_rejeita_transferencia_de_lancamento_fora_do_mes_anterior(self):
        ano3, mes3 = _mes_seguinte(self.ano2, self.mes2)
        criar_mes(ano3, mes3)
        # Lancamento no primeiro mes (nao imediatamente anterior ao terceiro mes)
        lancamento_dois_meses_atras = Lancamento.objects.create(
            descricao="Conta antiga",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=timezone.localdate() - timedelta(days=5),
            valor=Decimal("30.00"),
            conta=self.conta,
            competencia_ano=self.ano1,
            competencia_mes=self.mes1,
        )
        url = reverse("visualizacao:transferir_pendente", args=[lancamento_dois_meses_atras.pk])
        response = self.client.post(url, {"ano": str(ano3), "mes": str(mes3)})
        self.assertEqual(response.status_code, 400)
        lancamento_dois_meses_atras.refresh_from_db()
        self.assertEqual(lancamento_dois_meses_atras.competencia_mes, self.mes1)

    def test_rejeita_transferencia_de_lancamento_ja_pago(self):
        pago = Lancamento.objects.create(
            descricao="Conta paga",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=timezone.localdate() - timedelta(days=5),
            data_pagamento=timezone.localdate() - timedelta(days=4),
            valor=Decimal("30.00"),
            conta=self.conta,
            competencia_ano=self.ano1,
            competencia_mes=self.mes1,
        )
        url = reverse("visualizacao:transferir_pendente", args=[pago.pk])
        response = self.client.post(url, {"ano": str(self.ano2), "mes": str(self.mes2)})
        self.assertEqual(response.status_code, 400)


class ManterPendenteTests(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(
            nome="Banco MP",
            tipo=Conta.Tipo.BANCO,
            saldo_atual=Decimal("100.00"),
        )
        self.lancamento = Lancamento.objects.create(
            descricao="Conta mantida",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=date(2026, 3, 5),
            valor=Decimal("50.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=3,
        )

    def test_manter_pendente_retorna_refresh(self):
        url = reverse("visualizacao:manter_pendente", args=[self.lancamento.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.headers["HX-Refresh"], "true")

    def test_retorna_400_para_pk_inexistente(self):
        url = reverse("visualizacao:manter_pendente", args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)


class AjustarSaldoTests(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(
            nome="Banco AS",
            tipo=Conta.Tipo.BANCO,
            saldo_atual=Decimal("500.00"),
        )
        self.ano, self.mes = _mes_atual()
        criar_mes(self.ano, self.mes)

    def test_ajuste_valido_retorna_refresh(self):
        url = reverse("visualizacao:ajustar_saldo", args=[self.conta.pk])
        response = self.client.post(url, {"novo_saldo": "600.00", "ano": str(self.ano), "mes": str(self.mes)})
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.headers["HX-Refresh"], "true")

    def test_campo_ausente_retorna_400(self):
        url = reverse("visualizacao:ajustar_saldo", args=[self.conta.pk])
        response = self.client.post(url, {"ano": str(self.ano), "mes": str(self.mes)})
        self.assertEqual(response.status_code, 400)

    def test_decimal_invalido_retorna_400(self):
        url = reverse("visualizacao:ajustar_saldo", args=[self.conta.pk])
        response = self.client.post(url, {"novo_saldo": "abc", "ano": str(self.ano), "mes": str(self.mes)})
        self.assertEqual(response.status_code, 400)

    def test_campo_vazio_retorna_400(self):
        url = reverse("visualizacao:ajustar_saldo", args=[self.conta.pk])
        response = self.client.post(url, {"novo_saldo": "", "ano": str(self.ano), "mes": str(self.mes)})
        self.assertEqual(response.status_code, 400)

    def test_conta_inexistente_retorna_400(self):
        url = reverse("visualizacao:ajustar_saldo", args=[99999])
        response = self.client.post(url, {"novo_saldo": "100.00", "ano": str(self.ano), "mes": str(self.mes)})
        self.assertEqual(response.status_code, 400)

    def test_ajuste_gera_conciliacao_quando_necessario(self):
        Lancamento.objects.create(
            descricao="Entrada",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(self.ano, self.mes, 10),
            valor=Decimal("100.00"),
            conta=self.conta,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )
        url = reverse("visualizacao:ajustar_saldo", args=[self.conta.pk])
        response = self.client.post(url, {"novo_saldo": "450.00", "ano": str(self.ano), "mes": str(self.mes)})
        self.assertEqual(response.status_code, 204)
        self.assertTrue(
            Lancamento.objects.filter(conta=self.conta, tipo=Lancamento.Tipo.CONCILIACAO).exists()
        )


class CriarMesViewTests(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(nome="Banco CM", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("0.00"))
        self.ano, self.mes = _mes_atual()

    def test_cria_mes_e_redireciona(self):
        """Task 5.4: Criar o mes atual como primeiro mes redireciona corretamente."""
        url = reverse("visualizacao:criar_mes")
        response = self.client.post(url, {"ano": str(self.ano), "mes": str(self.mes)})
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"ano={self.ano}", response["Location"])
        self.assertIn(f"mes={self.mes}", response["Location"])

    def test_cria_mes_invalido_retorna_pagina_com_erro(self):
        """Task 5.4: Tentar criar mes fora da sequencia retorna mes_nao_criado com erro."""
        # Tentar criar um mes diferente do atual quando nenhum mes esta aberto
        hoje = date.today()
        ano_outro = hoje.year
        mes_outro = hoje.month - 1 if hoje.month > 1 else 12
        if mes_outro == 12 and hoje.month == 1:
            ano_outro -= 1
        url = reverse("visualizacao:criar_mes")
        response = self.client.post(url, {"ano": str(ano_outro), "mes": str(mes_outro)})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "visualizacao/mes_nao_criado.html")
        self.assertIn("erro_validacao", response.context)

    def test_cria_mes_com_pendentes_redireciona_para_resolucao(self):
        """Task 5.4: Criar mes seguinte com pendentes redireciona para resolucao."""
        criar_mes(self.ano, self.mes)
        ano2, mes2 = _mes_seguinte(self.ano, self.mes)
        Lancamento.objects.create(
            descricao="Conta atrasada",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=timezone.localdate() - timedelta(days=3),
            valor=Decimal("50.00"),
            conta=self.conta,
            competencia_ano=self.ano,
            competencia_mes=self.mes,
        )
        url = reverse("visualizacao:criar_mes")
        response = self.client.post(url, {"ano": str(ano2), "mes": str(mes2)})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("visualizacao:resolver_pendentes_abertura"), response["Location"])


class ResolverPendentesAberturaTests(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(nome="Banco RP", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("0.00"))
        self.ano1, self.mes1 = _mes_atual()
        self.ano2, self.mes2 = _mes_seguinte(self.ano1, self.mes1)
        criar_mes(self.ano1, self.mes1)
        self.pendente = Lancamento.objects.create(
            descricao="Conta atrasada",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=timezone.localdate() - timedelta(days=3),
            valor=Decimal("50.00"),
            conta=self.conta,
            competencia_ano=self.ano1,
            competencia_mes=self.mes1,
        )
        criar_mes(self.ano2, self.mes2)

    def test_exibe_pendentes_para_resolucao(self):
        url = reverse("visualizacao:resolver_pendentes_abertura")
        response = self.client.get(url, {"ano": str(self.ano2), "mes": str(self.mes2)})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Conta atrasada")

    def test_redireciona_quando_nao_ha_pendentes(self):
        transferir_pendente_para_mes(self.pendente, self.ano2, self.mes2)
        url = reverse("visualizacao:resolver_pendentes_abertura")
        response = self.client.get(url, {"ano": str(self.ano2), "mes": str(self.mes2)})
        self.assertEqual(response.status_code, 302)
