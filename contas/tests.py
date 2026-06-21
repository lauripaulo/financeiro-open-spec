from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

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


class ContaViewTests(TestCase):
    def test_listar_contas(self):
        Conta.objects.create(nome="Banco Lista", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("10.00"))
        response = self.client.get(reverse("contas:listar"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Banco Lista")

    def test_criar_conta_banco(self):
        url = reverse("contas:criar")
        response = self.client.post(
            url,
            {
                "nome": "Banco Novo",
                "tipo": Conta.Tipo.BANCO,
                "saldo_atual": "100.00",
                "limite_negativo": "300.00",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Conta.objects.filter(nome="Banco Novo").exists())

    def test_criar_conta_invalida_reexibe_formulario_com_erro(self):
        url = reverse("contas:criar")
        response = self.client.post(
            url,
            {"nome": "Banco Sem Saldo", "tipo": Conta.Tipo.BANCO},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Conta.objects.filter(nome="Banco Sem Saldo").exists())
        self.assertTrue(response.context["form"].errors)

    def test_editar_conta(self):
        conta = Conta.objects.create(nome="Banco Editar", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("10.00"))
        url = reverse("contas:editar", args=[conta.pk])
        response = self.client.post(
            url,
            {
                "nome": "Banco Editado",
                "tipo": Conta.Tipo.BANCO,
                "saldo_atual": "20.00",
                "limite_negativo": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        conta.refresh_from_db()
        self.assertEqual(conta.nome, "Banco Editado")

    def test_excluir_conta_sem_lancamentos(self):
        conta = Conta.objects.create(nome="Banco Excluir", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("10.00"))
        url = reverse("contas:excluir", args=[conta.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Conta.objects.filter(pk=conta.pk).exists())

    def test_excluir_conta_com_lancamentos_exibe_mensagem_de_bloqueio(self):
        conta = Conta.objects.create(nome="Banco Bloqueado", tipo=Conta.Tipo.BANCO, saldo_atual=Decimal("10.00"))
        Lancamento.objects.create(
            descricao="Aluguel",
            tipo=Lancamento.Tipo.GASTO_FIXO,
            data_vencimento="2026-01-10",
            valor=Decimal("50.00"),
            conta=conta,
            competencia_ano=2026,
            competencia_mes=1,
        )
        url = reverse("contas:excluir", args=[conta.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Conta.objects.filter(pk=conta.pk).exists())
        self.assertContains(response, "nao pode ser excluida")
