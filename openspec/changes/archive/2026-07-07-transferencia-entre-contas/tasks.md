## 1. Model

- [x] 1.1 Adicionar `TRANSFERENCIA_ENVIADA` e `TRANSFERENCIA_RECEBIDA` ao enum `Lancamento.Tipo` em `lancamentos/models.py`
- [x] 1.2 Adicionar `TRANSFERENCIA_RECEBIDA` a `TIPOS_ENTRADA` e `TRANSFERENCIA_ENVIADA` a `TIPOS_SAIDA`
- [x] 1.3 Gerar migration (`makemigrations lancamentos`) e verificar que nao ha DDL de schema

## 2. Service

- [x] 2.1 Criar `gerar_transferencia()` em `lancamentos/services.py`: recebe `conta_origem`, `conta_destino`, `valor`, `data_vencimento`, `descricao`; cria o par em `transaction.atomic`; retorna `(enviada, recebida)`
- [x] 2.2 Validar na service que `conta_origem != conta_destino` e que nenhuma e INVESTIMENTO

## 3. Form

- [x] 3.1 Adicionar `TRANSFERENCIA_ENVIADA` e `TRANSFERENCIA_RECEBIDA` a `TIPOS_EXCLUIDOS_DO_CADASTRO_MANUAL` em `LancamentoForm`
- [x] 3.2 Criar `TransferenciaForm` em `lancamentos/forms.py` com campos: `conta_origem`, `conta_destino` (somente BANCO/CARTAO), `valor`, `data_vencimento`, `descricao`
- [x] 3.3 Implementar `TransferenciaForm.clean()`: rejeitar contas iguais; rejeitar INVESTIMENTO
- [x] 3.4 Implementar `TransferenciaForm.save()` chamando `gerar_transferencia()`

## 4. View e URL

- [x] 4.1 Criar view `criar_transferencia` em `lancamentos/views.py` (GET exibe form; POST valida, salva, emite `messages.success`, redireciona)
- [x] 4.2 Registrar URL `parcelado/transferencia/` → `criar_transferencia` com nome `transferencia` em `lancamentos/urls.py`

## 5. Template

- [x] 5.1 Criar `templates/lancamentos/form_transferencia.html` com campos do `TransferenciaForm` e botao de submit
- [x] 5.2 Adicionar link "Nova transferencia" na `templates/visualizacao/consolidada.html` ao lado de "Nova compra parcelada"

## 6. Testes

- [x] 6.1 Testar `gerar_transferencia()`: par criado, valores iguais, lancamentos vinculados, tipos corretos
- [x] 6.2 Testar validacao da service: mesma conta rejeitada; INVESTIMENTO rejeitado
- [x] 6.3 Testar `TransferenciaForm.clean()` para contas iguais e para conta INVESTIMENTO
- [x] 6.4 Testar view POST valido: redirect 302, mensagem de sucesso, par criado no banco
- [x] 6.5 Testar que `TRANSFERENCIA_ENVIADA` e `TRANSFERENCIA_RECEBIDA` nao aparecem no formulario manual de lancamento
- [x] 6.6 Testar que abertura de mes nao propaga `TRANSFERENCIA_ENVIADA`
