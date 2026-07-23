## 1. Baseline e Auditoria

- [x] 1.1 Gerar relatorio final de cobertura com `coverage run manage.py test && coverage report -m`.
- [x] 1.2 Documentar as 104 linhas `Missing` classificadas por app: testavel, codigo morto ou migracao reversa.
- [x] 1.3 Resolver classificacao de codigo morto (remover ou simplificar) antes de escrever testes.

## 2. Cobertura de arquivos de projeto

- [x] 2.1 Testar branches de `manage.py` (linhas 12-13).
- [x] 2.2 Testar branch nao coberta de `financeiro/settings.py` (linha 40).

## 3. Cobertura do app `contas`

- [x] 3.1 Cobrir ramos de `Conta.clean()` para tipos `CARTAO`, `BANCO` e `INVESTIMENTO` (linhas 37, 39, 41, 47, 53, 55, 58, 61 de `contas/models.py`).
- [x] 3.2 Cobrir casos faltantes de `MoedaWidget` (linhas 21, 29-30 de `contas/widgets.py`).
- [x] 3.3 Adicionar teste de reversao da migracao `0002_alter_conta_limite_negativo` (linhas 9-10) ou justificar por ser no-op.

## 4. Cobertura do app `lancamentos`

- [x] 4.1 Cobrir branches faltantes de `LancamentoForm.clean()` (linhas 56, 59, 65, 74 de `lancamentos/forms.py`).
- [x] 4.2 Cobrir branches faltantes de `CompraParceladaForm.clean()` (linhas 100, 103 de `lancamentos/forms.py`).
- [x] 4.3 Cobrir metodos/propriedades nao testados de `Lancamento` (linhas 12, 15-16, 23-30, 34, 46, 131, 144, 149, 164, 169-170, 184, 186, 188, 191, 194, 197, 201, 210-211, 250 de `lancamentos/models.py`).
- [x] 4.4 Cobrir helpers `_erro` e caminhos htmx/erro das views (linhas 16-19, 45, 58, 92-93, 108, 121-122, 153, 176 de `lancamentos/views.py`).

## 5. Cobertura do app `meses`

- [x] 5.1 Cobrir branches faltantes de `Mes` e `SaldoMensalConta` (linhas 24-25, 42, 45-46 de `meses/models.py`).
- [x] 5.2 Cobrir caminhos defensivos de `meses/services.py` (linhas 17, 23, 158, 209, 276, 282, 306, 327-330).
- [x] 5.3 Cobrir linha faltante do teste helper em `meses/tests.py` (linha 320), se for codigo de teste util.

## 6. Cobertura do app `parcelas`

- [x] 6.1 Cobrir propriedades e choices de `CompraParcelada` (linhas 32, 35-44, 48 de `parcelas/models.py`).

## 7. Cobertura do app `visualizacao`

- [x] 7.1 Cobrir branches faltantes de `visualizacao/services.py` (linhas 88, 168-169).
- [x] 7.2 Cobrir caminhos das views de `visualizacao/views.py` (linhas 35-36, 56-57, 196, 202, 304).
- [x] 7.3 Cobrir helpers/linhas faltantes em `visualizacao/tests.py` (linhas 24, 56, 748), se aplicavel.

## 8. Cobertura do app `importacao`

- [x] 8.1 Adicionar teste de reversao da migracao `0002_encurtar_descricoes_importadas` (linha 14) ou justificar por ser no-op.

## 9. Verificacao Final

- [x] 9.1 Executar `.venv/bin/coverage run manage.py test` e confirmar `TOTAL` com 100%.
- [x] 9.2 Executar `.venv/bin/python manage.py test` sem `coverage` para garantir que todos os testes passam.
- [x] 9.3 Executar `openspec validate --changes` e confirmar aprovacao.
