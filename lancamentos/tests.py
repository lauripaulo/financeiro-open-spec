from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from contas.models import Conta
from lancamentos.forms import LancamentoForm
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


class LancamentoFormTiposExcluidosTests(TestCase):
    def setUp(self):
        self.conta_cartao = Conta.objects.create(nome="Cartao Form", tipo=Conta.Tipo.CARTAO, dia_vencimento=10)

    def test_conciliacao_nao_esta_nas_opcoes(self):
        form = LancamentoForm()
        valores = [escolha[0] for escolha in form.fields["tipo"].choices]
        self.assertNotIn(Lancamento.Tipo.CONCILIACAO, valores)

    def test_parcela_cartao_nao_esta_nas_opcoes(self):
        form = LancamentoForm()
        valores = [escolha[0] for escolha in form.fields["tipo"].choices]
        self.assertNotIn(Lancamento.Tipo.PARCELA_CARTAO, valores)

    def test_submissao_manual_de_parcela_cartao_e_rejeitada(self):
        hoje = date.today()
        instancia = Lancamento(competencia_ano=hoje.year, competencia_mes=hoje.month)
        form = LancamentoForm(
            data={
                "descricao": "Parcela manual",
                "tipo": Lancamento.Tipo.PARCELA_CARTAO,
                "data_vencimento": hoje,
                "valor": "50.00",
                "conta": self.conta_cartao.pk,
            },
            instance=instancia,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("tipo", form.errors)
        self.assertFalse(Lancamento.objects.filter(tipo=Lancamento.Tipo.PARCELA_CARTAO).exists())


class CriarLancamentoViewTests(TestCase):
    def setUp(self):
        self.conta = Conta.objects.create(nome="Banco Criar", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("0.00"))

    def test_criar_lancamento_valido_nao_levanta_erro(self):
        hoje = date.today()
        url = f"{reverse('lancamentos:criar')}?ano={hoje.year}&mes={hoje.month}"
        response = self.client.post(
            url,
            {
                "descricao": "Aluguel",
                "tipo": Lancamento.Tipo.GASTO_FIXO,
                "data_vencimento": hoje.isoformat(),
                "valor": "50.00",
                "conta": self.conta.pk,
            },
        )
        self.assertEqual(response.status_code, 302)
        lancamento = Lancamento.objects.get(descricao="Aluguel")
        self.assertEqual(lancamento.competencia_ano, hoje.year)
        self.assertEqual(lancamento.competencia_mes, hoje.month)

    def test_criar_lancamento_invalido_reexibe_formulario_sem_erro_de_competencia(self):
        hoje = date.today()
        url = reverse("lancamentos:criar")
        response = self.client.post(
            url,
            {
                "descricao": "",
                "tipo": Lancamento.Tipo.GASTO_FIXO,
                "data_vencimento": hoje.isoformat(),
                "valor": "50.00",
                "conta": self.conta.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("descricao", response.context["form"].errors)
