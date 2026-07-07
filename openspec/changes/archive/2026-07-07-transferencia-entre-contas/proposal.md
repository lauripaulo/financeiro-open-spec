## Why

Não existe forma de registrar uma transferência de dinheiro entre contas operacionais (BANCO/CARTAO). O usuário precisava criar dois lançamentos desconexos manualmente, o que gerava inconsistências no saldo e dificultava o rastreio da operação.

## What Changes

- Dois novos tipos de lançamento: `TRANSFERENCIA_ENVIADA` (saída) e `TRANSFERENCIA_RECEBIDA` (entrada)
- Formulário dedicado para criar transferências atomicamente (um submit cria o par vinculado)
- Ambos os tipos são bloqueados de criação manual no formulário genérico de lançamento
- Contas do tipo INVESTIMENTO são excluídas — esse fluxo já é coberto por APORTE/RESGATE

## Capabilities

### New Capabilities
- `transferencia`: Criação de transferências entre contas BANCO e CARTAO via formulário dedicado, gerando um par de lançamentos vinculados (`TRANSFERENCIA_ENVIADA` + `TRANSFERENCIA_RECEBIDA`) em `transaction.atomic`

### Modified Capabilities
- `lancamentos`: Dois novos valores no enum `Tipo`; `TRANSFERENCIA_RECEBIDA` entra em `TIPOS_ENTRADA`, `TRANSFERENCIA_ENVIADA` em `TIPOS_SAIDA`; ambos adicionados a `TIPOS_EXCLUIDOS_DO_CADASTRO_MANUAL`
- `lancamento-vinculado`: A validação de par vinculado (valores iguais, contas diferentes) passa a cobrir também pares de transferência

## Impact

- `lancamentos/models.py` — novos `Tipo` values e sets `TIPOS_ENTRADA`/`TIPOS_SAIDA`
- `lancamentos/forms.py` — novo `TransferenciaForm`; `TIPOS_EXCLUIDOS_DO_CADASTRO_MANUAL` atualizado
- `lancamentos/views.py` + `urls.py` — nova view `criar_transferencia`
- `lancamentos/services.py` — nova função `gerar_transferencia()`
- `templates/lancamentos/form_transferencia.html` — novo template
- Migration vazia (TextChoices não altera schema SQLite)
- `lancamentos/tests.py` — testes de criação, validação e bloqueio de criação manual
