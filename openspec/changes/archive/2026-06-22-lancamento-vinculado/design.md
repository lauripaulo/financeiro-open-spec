## Context

O sistema registra aportes, resgates e transferências entre contas como lançamentos
completamente independentes — sem nenhum vínculo estrutural entre os dois lados de uma
mesma operação financeira. O modelo atual de `Lancamento` possui um único FK de conta
(`conta`), representando apenas o lado ao qual o lançamento pertence.

O padrão de auto-FK já existe no codebase: `grupo_recorrencia` é uma auto-FK nullable
em `Lancamento` que liga instâncias de uma série recorrente. O campo `lancamento_vinculado`
segue exatamente esse padrão.

## Goals / Non-Goals

**Goals:**
- Adicionar campo `lancamento_vinculado` (auto-FK nullable) ao modelo `Lancamento`
- Sincronização bidirecional automática no `save()` com guard contra recursão infinita
- Validação: bloquear vínculo quando `|valor A| ≠ |valor B|`
- Aviso na view ao excluir lançamento que possui par vinculado
- Expor o campo nos formulários de criação e edição de lançamentos
- Exibir coluna "Contraparte" na visão consolidada
- Exibir conta bancária de origem/destino na visão patrimônio

**Non-Goals:**
- Geração automática do lançamento par (usuário continua criando os dois manualmente)
- Restrição de tipo (qualquer lançamento pode ser vinculado a qualquer outro)
- Migração automática de aportes históricos para pares vinculados

## Decisions

### Decisão 1: Auto-FK em Lancamento, não um novo modelo

**Escolhido:** campo `lancamento_vinculado = FK('self', null=True, on_delete=SET_NULL)` no
modelo existente.

**Alternativa considerada:** novo modelo `Transferencia` com dois FKs para `Lancamento`
(origem e destino). Mais explícito estruturalmente, mas adiciona complexidade
desnecessária — introduz uma nova entidade para um dado que é essencialmente metadado
de rastreamento sobre entradas existentes.

**Por que o auto-FK:** consistente com o padrão já estabelecido de `grupo_recorrencia`.
Sem nova tabela, sem novo modelo, sem novo conceito de domínio.

### Decisão 2: Sincronização bidirecional no save() com guard de ciclo

**Escolhido:** no `Lancamento.save()`, ao detectar que `lancamento_vinculado` mudou
para um valor B, verificar se `B.lancamento_vinculado` já aponta para `self`. Se não
apontar, atualizar `B.lancamento_vinculado = self` via `B.save(update_fields=['lancamento_vinculado'])`.
O guard de ciclo é: só atualizar B se B ainda não aponta para A — isso quebra a recursão
sem necessidade de flag em thread-local.

Da mesma forma, ao limpar o vínculo (setar para null) ou trocá-lo, limpar o lado
anterior antes de setar o novo.

**Por que no save() e não no service layer:** consistente com como `grupo_recorrencia`
opera. A lógica de integridade do par pertence ao próprio modelo.

### Decisão 3: Validação de valor em clean()

O sistema bloqueia o vínculo quando `|lancamento_vinculado.valor| ≠ |self.valor|`.
Validado em `Lancamento.clean()` e reforçado no form. O erro é exposto ao usuário com
mensagem clara antes de qualquer save.

### Decisão 4: Aviso de exclusão na view, não no modelo

O modelo usa `on_delete=SET_NULL`, mantendo integridade referencial sem bloquear a
exclusão no banco. O aviso ao usuário é implementado na view de exclusão: antes de
processar o DELETE, verificar `lancamento.lancamento_vinculado` e apresentar
confirmação com opções "excluir somente este" / "excluir os dois".

**Por que na view e não no modelo:** evitar acoplar lógica de UX ao modelo. O `clean()`
e `delete()` do modelo não sabem de contexto de request.

### Decisão 5: Escopo aberto — qualquer par de lançamentos

Não há restrição de tipo. O campo funciona para:
- `APORTE` (Investimento) ↔ `GASTO_VARIAVEL` (Banco) — aporte investimento
- `RESGATE` (Investimento) ↔ `RECEBIMENTO_EXCEPCIONAL` (Banco) — resgate investimento
- `GASTO_VARIAVEL` (Banco A) ↔ `RECEBIMENTO_EXCEPCIONAL` (Banco B) — transferência entre bancos

## Risks / Trade-offs

- **Recursão no save()** → Mitigado pelo guard de ciclo: só atualiza B se B.lancamento_vinculado ≠ A
- **Exclusão via admin/shell não exibe aviso** → Aceitável em sistema single-user; o SET_NULL preserva integridade do banco
- **Valores editados após vínculo criado podem divergir** → A validação ocorre no momento do vínculo; edições posteriores do valor não revalidam o par automaticamente. Risco baixo, pode ser revisitado
- **Vincular lançamentos de meses encerrados requer confirmação** → O fluxo de edição em mês encerrado já exige confirmação do usuário; o campo `lancamento_vinculado` não altera esse comportamento
