from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from contas.models import Conta
from lancamentos.models import Lancamento
from meses.services import criar_mes
from visualizacao.views import _filtros_mes


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


class VisaoConsolidadaTests(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(
            nome="Banco Teste",
            tipo=Conta.Tipo.BANCO,
            saldo_atual=Decimal("500.00"),
        )
        criar_mes(2026, 4)
        self.url = reverse("visualizacao:consolidada")

    def test_mes_nao_criado_renderiza_pagina_especifica(self):
        response = self.client.get(self.url, {"ano": "2030", "mes": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "visualizacao/mes_nao_criado.html")

    def test_mes_criado_renderiza_consolidada(self):
        response = self.client.get(self.url, {"ano": "2026", "mes": "4"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "visualizacao/consolidada.html")

    def test_filtra_por_conta(self):
        outra = Conta.objects.create(nome="Outro Banco", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("0.00"))
        Lancamento.objects.create(
            descricao="Entrada conta principal",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(2026, 4, 10),
            valor=Decimal("100.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=4,
        )
        Lancamento.objects.create(
            descricao="Entrada outra conta",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(2026, 4, 10),
            valor=Decimal("200.00"),
            conta=outra,
            competencia_ano=2026,
            competencia_mes=4,
        )
        response = self.client.get(self.url, {"ano": "2026", "mes": "4", "conta": str(self.conta.pk)})
        self.assertEqual(response.status_code, 200)
        lancamentos = response.context["lancamentos"]
        self.assertTrue(all(l.conta_id == self.conta.pk for l in lancamentos))

    def test_filtra_por_status_pago(self):
        Lancamento.objects.create(
            descricao="Pago",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(2026, 4, 1),
            data_pagamento=date(2026, 4, 1),
            valor=Decimal("50.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=4,
        )
        Lancamento.objects.create(
            descricao="Nao pago",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(2026, 4, 30),
            valor=Decimal("50.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=4,
        )
        response = self.client.get(self.url, {"ano": "2026", "mes": "4", "status": "PAGO"})
        self.assertEqual(response.status_code, 200)
        lancamentos = response.context["lancamentos"]
        self.assertTrue(all(l.status == Lancamento.Status.PAGO for l in lancamentos))
        self.assertEqual(len(lancamentos), 1)

    def test_totais_entradas_e_saidas(self):
        Lancamento.objects.create(
            descricao="Salario",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(2026, 4, 5),
            valor=Decimal("1000.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=4,
        )
        Lancamento.objects.create(
            descricao="Aluguel",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=date(2026, 4, 10),
            valor=Decimal("300.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=4,
        )
        response = self.client.get(self.url, {"ano": "2026", "mes": "4"})
        self.assertEqual(response.context["total_entradas"], Decimal("1000.00"))
        self.assertEqual(response.context["total_saidas"], Decimal("300.00"))


class TransferirPendenteTests(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(
            nome="Banco TP",
            tipo=Conta.Tipo.BANCO,
            saldo_atual=Decimal("100.00"),
        )
        criar_mes(2026, 3)
        criar_mes(2026, 4)
        self.lancamento = Lancamento.objects.create(
            descricao="Conta atrasada",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento=date(2026, 3, 5),
            valor=Decimal("80.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=3,
        )

    def test_transfere_lancamento_para_mes_atual(self):
        url = reverse("visualizacao:transferir_pendente", args=[self.lancamento.pk])
        response = self.client.post(url, {"ano": "2026", "mes": "4"})
        self.assertEqual(response.status_code, 200)
        self.lancamento.refresh_from_db()
        self.assertEqual(self.lancamento.competencia_mes, 4)
        self.assertEqual(self.lancamento.competencia_ano, 2026)

    def test_retorna_400_para_pk_inexistente(self):
        url = reverse("visualizacao:transferir_pendente", args=[99999])
        response = self.client.post(url, {"ano": "2026", "mes": "4"})
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

    def test_manter_pendente_retorna_flash(self):
        url = reverse("visualizacao:manter_pendente", args=[self.lancamento.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "visualizacao/_flash.html")

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
        criar_mes(2026, 4)

    def test_ajuste_valido_retorna_flash(self):
        url = reverse("visualizacao:ajustar_saldo", args=[self.conta.pk])
        response = self.client.post(url, {"novo_saldo": "600.00", "ano": "2026", "mes": "4"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "visualizacao/_flash.html")

    def test_campo_ausente_retorna_400(self):
        url = reverse("visualizacao:ajustar_saldo", args=[self.conta.pk])
        response = self.client.post(url, {"ano": "2026", "mes": "4"})
        self.assertEqual(response.status_code, 400)

    def test_decimal_invalido_retorna_400(self):
        url = reverse("visualizacao:ajustar_saldo", args=[self.conta.pk])
        response = self.client.post(url, {"novo_saldo": "abc", "ano": "2026", "mes": "4"})
        self.assertEqual(response.status_code, 400)

    def test_campo_vazio_retorna_400(self):
        url = reverse("visualizacao:ajustar_saldo", args=[self.conta.pk])
        response = self.client.post(url, {"novo_saldo": "", "ano": "2026", "mes": "4"})
        self.assertEqual(response.status_code, 400)

    def test_conta_inexistente_retorna_400(self):
        url = reverse("visualizacao:ajustar_saldo", args=[99999])
        response = self.client.post(url, {"novo_saldo": "100.00", "ano": "2026", "mes": "4"})
        self.assertEqual(response.status_code, 400)

    def test_ajuste_gera_conciliacao_quando_necessario(self):
        Lancamento.objects.create(
            descricao="Entrada",
            tipo=Lancamento.Tipo.RECEBIMENTO_FIXO,
            data_vencimento=date(2026, 4, 10),
            valor=Decimal("100.00"),
            conta=self.conta,
            competencia_ano=2026,
            competencia_mes=4,
        )
        url = reverse("visualizacao:ajustar_saldo", args=[self.conta.pk])
        response = self.client.post(url, {"novo_saldo": "450.00", "ano": "2026", "mes": "4"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Lancamento.objects.filter(conta=self.conta, tipo=Lancamento.Tipo.CONCILIACAO).exists()
        )


class CriarMesViewTests(TestCase):
    def setUp(self):
        Conta.objects.create(nome="Banco CM", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("0.00"))

    def test_cria_mes_e_redireciona(self):
        url = reverse("visualizacao:criar_mes")
        response = self.client.post(url, {"ano": "2026", "mes": "5"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("ano=2026", response["Location"])
        self.assertIn("mes=5", response["Location"])
