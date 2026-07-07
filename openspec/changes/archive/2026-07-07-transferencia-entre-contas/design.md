## Context

O sistema já possui `lancamento_vinculado`, um FK bidirecional que liga dois lançamentos como par de uma mesma operação financeira. APORTE e RESGATE usam esse mecanismo para representar movimentação entre conta BANCO e conta INVESTIMENTO. Não existe, porém, nenhum tipo dedicado para transferências entre contas operacionais (BANCO/CARTAO).

O padrão atual de criação de pares vinculados via formulário manual tem um gap: o usuário precisa criar dois lançamentos separados e depois vinculá-los. Para o caso de investimento isso é tolerado porque APORTE e RESGATE são tipos distintos e a validação de valores iguais já existe. Para TRANSFERENCIA, o formulário dedicado elimina esse risco.

## Goals / Non-Goals

**Goals:**
- Dois novos tipos: `TRANSFERENCIA_ENVIADA` (saída) e `TRANSFERENCIA_RECEBIDA` (entrada)
- Formulário dedicado que cria o par atomicamente em `transaction.atomic`
- Contas BANCO e CARTAO permitidas; INVESTIMENTO excluído
- Ambos os tipos bloqueados de criação manual no formulário genérico

**Non-Goals:**
- Recorrência/propagação de transferências
- Formulário de edição dedicado para transferências (o formulário existente de lançamento é suficiente, com a validação de valores iguais já existente)
- Suporte a INVESTIMENTO nesse fluxo (coberto por APORTE/RESGATE)

## Decisions

### D1: Dois tipos distintos em vez de tipo único com direção inferida

`TRANSFERENCIA_ENVIADA` entra em `TIPOS_SAIDA` e `TRANSFERENCIA_RECEBIDA` em `TIPOS_ENTRADA`. Segue exatamente o padrão APORTE/RESGATE. Alternativa descartada: tipo único `TRANSFERENCIA` fora dos sets — exigiria tratamento especial em todo cálculo de saldo.

### D2: Service function `gerar_transferencia()` em `lancamentos/services.py`

Análoga a `gerar_parcelas_da_compra()` em `parcelas/services.py`. Cria os dois lançamentos em `transaction.atomic` e retorna a tupla `(enviada, recebida)`. Centraliza a lógica e facilita testes.

### D3: Restrição de conta via validação no form, não no model

A regra "sem INVESTIMENTO" é aplicada em `TransferenciaForm.clean()`. O model não impõe a restrição para não criar acoplamento desnecessário entre o tipo de conta e o tipo de lançamento no nível de `full_clean()`.

### D4: Sem migration de schema

`TextChoices` em Django são armazenados como varchar. Novos valores não alteram o schema SQLite — o Django detecta a mudança como `AlterField` sem DDL. Uma migration vazia (ou com `AlterField` apenas) é suficiente.

## Risks / Trade-offs

- [Risco] Usuário exclui um lado da transferência e fica com par incompleto → Mitigação: comportamento existente de `excluir_par` já trata isso (aviso + opção de excluir ambos).
- [Risco] Relatórios/filtros existentes ignoram os novos tipos → Mitigação: por serem adicionados a `TIPOS_ENTRADA`/`TIPOS_SAIDA`, todos os cálculos de saldo os incorporam automaticamente.
- [Trade-off] Não há formulário dedicado de edição → usuário pode editar valor de um lado sem atualizar o outro; a validação existente (`abs(valor)` iguais) rejeita o divergente mas não sincroniza automaticamente. Aceito por ora.
