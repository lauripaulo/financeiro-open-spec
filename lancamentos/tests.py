from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from contas.models import Conta
from lancamentos.forms import LancamentoForm
from lancamentos.models import Lancamento


def _make_banco(nome="Banco", saldo=Decimal("1000.00")):
    return Conta.objects.create(nome=nome, tipo=Conta.Tipo.BANCO, saldo_atual=saldo, limite_negativo=Decimal("200.00"))


def _make_investimento(nome="Invest", saldo=Decimal("5000.00")):
    return Conta.objects.create(nome=nome, tipo=Conta.Tipo.INVESTIMENTO, saldo_atual=saldo)


def _make_lancamento(conta, tipo=None, valor=Decimal("500.00"), descricao="Lancamento"):
    hoje = date.today()
    tipo = tipo or (Lancamento.Tipo.APORTE if conta.tipo == Conta.Tipo.INVESTIMENTO else Lancamento.Tipo.GASTO_VARIAVEL)
    return Lancamento.objects.create(
        descricao=descricao,
        tipo=tipo,
        data_vencimento=hoje,
        valor=valor,
        conta=conta,
        competencia_ano=hoje.year,
        competencia_mes=hoje.month,
    )


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

    def test_form_aporte_em_conta_nao_investimento_nao_gera_relatedobjectdoesnotexist(self):
        hoje = date.today()
        instancia = Lancamento(competencia_ano=hoje.year, competencia_mes=hoje.month)
        form = LancamentoForm(
            data={
                "descricao": "Aporte invalido",
                "tipo": Lancamento.Tipo.APORTE,
                "data_vencimento": hoje.isoformat(),
                "valor": "10.00",
                "conta": self.conta.pk,
            },
            instance=instancia,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("conta", form.errors)

    def test_criar_lancamento_aporte_invalido_retorna_200_com_erros(self):
        hoje = date.today()
        url = f"{reverse('lancamentos:criar')}?ano={hoje.year}&mes={hoje.month}"
        response = self.client.post(
            url,
            {
                "descricao": "Aporte invalido",
                "tipo": Lancamento.Tipo.APORTE,
                "data_vencimento": hoje.isoformat(),
                "valor": "10.00",
                "conta": self.conta.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("conta", response.context["form"].errors)


# ---------------------------------------------------------------------------
# Testes: lancamento_vinculado — sincronização bidirecional
# ---------------------------------------------------------------------------

class LancamentoVinculadoSyncTests(TestCase):
    def setUp(self):
        self.banco = _make_banco()
        self.invest = _make_investimento()

    def test_6_1_setar_vinculo_em_a_sincroniza_b(self):
        """6.1 Setar A.lancamento_vinculado = B deve sincronizar B.lancamento_vinculado = A."""
        a = _make_lancamento(self.banco, valor=Decimal("500.00"))
        b = _make_lancamento(self.invest, valor=Decimal("500.00"))

        a.lancamento_vinculado = b
        a.save()

        b.refresh_from_db()
        self.assertEqual(b.lancamento_vinculado_id, a.pk)

    def test_6_2_trocar_vinculo_limpa_b_e_seta_c(self):
        """6.2 Trocar A de B para C limpa B e define C.lancamento_vinculado = A."""
        a = _make_lancamento(self.banco, valor=Decimal("500.00"))
        b = _make_lancamento(self.invest, valor=Decimal("500.00"), descricao="B")
        c = _make_lancamento(self.invest, valor=Decimal("500.00"), descricao="C")

        a.lancamento_vinculado = b
        a.save()

        a.lancamento_vinculado = c
        a.save()

        b.refresh_from_db()
        c.refresh_from_db()
        self.assertIsNone(b.lancamento_vinculado_id)
        self.assertEqual(c.lancamento_vinculado_id, a.pk)

    def test_6_3_remover_vinculo_limpa_b(self):
        """6.3 Remover A.lancamento_vinculado deve limpar B.lancamento_vinculado."""
        a = _make_lancamento(self.banco, valor=Decimal("500.00"))
        b = _make_lancamento(self.invest, valor=Decimal("500.00"))

        a.lancamento_vinculado = b
        a.save()

        a.lancamento_vinculado = None
        a.save()

        b.refresh_from_db()
        self.assertIsNone(b.lancamento_vinculado_id)


# ---------------------------------------------------------------------------
# Testes: lancamento_vinculado — validação de valor
# ---------------------------------------------------------------------------

class LancamentoVinculadoValidacaoTests(TestCase):
    def setUp(self):
        self.banco = _make_banco()
        self.invest = _make_investimento()

    def test_6_4_vinculo_bloqueado_quando_valores_diferem(self):
        """6.4 Vincular lançamentos com valores absolutos diferentes deve lançar ValidationError."""
        a = _make_lancamento(self.banco, valor=Decimal("500.00"))
        b = _make_lancamento(self.invest, valor=Decimal("400.00"))

        a.lancamento_vinculado = b
        with self.assertRaises(ValidationError) as ctx:
            a.save()
        self.assertIn("lancamento_vinculado", ctx.exception.message_dict)

    def test_6_5_vinculo_aceito_quando_valores_absolutos_iguais(self):
        """6.5 Vincular lançamentos com mesmo valor absoluto deve ser aceito."""
        a = _make_lancamento(self.banco, valor=Decimal("500.00"))
        b = _make_lancamento(self.invest, valor=Decimal("500.00"))

        a.lancamento_vinculado = b
        a.save()  # deve não lançar exceção

        a.refresh_from_db()
        self.assertEqual(a.lancamento_vinculado_id, b.pk)


# ---------------------------------------------------------------------------
# Testes: lancamento_vinculado — comportamento de exclusão na view
# ---------------------------------------------------------------------------

class LancamentoVinculadoExclusaoViewTests(TestCase):
    def setUp(self):
        self.banco = _make_banco()
        self.invest = _make_investimento()

    def _criar_par(self, valor=Decimal("500.00")):
        a = _make_lancamento(self.banco, valor=valor, descricao="Saida Banco")
        b = _make_lancamento(self.invest, valor=valor, descricao="Aporte Invest")
        a.lancamento_vinculado = b
        a.save()
        a.refresh_from_db()
        b.refresh_from_db()
        return a, b

    def test_6_6_exclusao_com_par_exibe_confirmacao(self):
        """6.6 A view de exclusão deve exibir aviso quando o lançamento possui par vinculado."""
        a, b = self._criar_par()
        url = reverse("lancamentos:excluir", args=[a.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "vinculado")
        self.assertContains(response, b.descricao)

    def test_6_7_excluir_os_dois_remove_ambos(self):
        """6.7 Excluir os dois deve remover ambos os lançamentos do par."""
        a, b = self._criar_par()
        url = reverse("lancamentos:excluir_par", args=[a.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Lancamento.objects.filter(pk=a.pk).exists())
        self.assertFalse(Lancamento.objects.filter(pk=b.pk).exists())

    def test_6_8_excluir_somente_este_limpa_vinculo_do_sobrevivente(self):
        """6.8 Excluir somente este deve remover apenas A e limpar lancamento_vinculado de B."""
        a, b = self._criar_par()
        url = reverse("lancamentos:excluir", args=[a.pk])
        response = self.client.post(url, {"ignorar_par": "1"})
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Lancamento.objects.filter(pk=a.pk).exists())
        b.refresh_from_db()
        self.assertIsNone(b.lancamento_vinculado_id)


# ---------------------------------------------------------------------------
# Testes: lancamento_vinculado — visão consolidada e patrimônio
# ---------------------------------------------------------------------------

class LancamentoVinculadoVisualizacaoTests(TestCase):
    def setUp(self):
        from meses.services import criar_mes
        hoje = date.today()
        self.banco = _make_banco(nome="Banco Inter")
        self.invest = _make_investimento(nome="Previdencia XP")
        criar_mes(hoje.year, hoje.month)
        self.hoje = hoje

    def _criar_par_vinculado(self):
        saida = _make_lancamento(self.banco, valor=Decimal("500.00"), descricao="Aporte Prev")
        aporte = _make_lancamento(self.invest, valor=Decimal("500.00"), descricao="Aporte Prev")
        saida.lancamento_vinculado = aporte
        saida.save()
        saida.refresh_from_db()
        aporte.refresh_from_db()
        return saida, aporte

    def test_6_9_consolidada_inclui_conta_contraparte(self):
        """6.9 A visão consolidada deve exibir a conta contraparte para lançamentos vinculados."""
        saida, aporte = self._criar_par_vinculado()
        url = f"/?ano={self.hoje.year}&mes={self.hoje.month}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Previdencia XP")

    def test_6_10_patrimonio_exibe_conta_bancaria_para_aportes_vinculados(self):
        """6.10 A visão patrimônio deve exibir a conta bancária de aportes vinculados."""
        saida, aporte = self._criar_par_vinculado()
        url = reverse("visualizacao:patrimonio")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Banco Inter")
