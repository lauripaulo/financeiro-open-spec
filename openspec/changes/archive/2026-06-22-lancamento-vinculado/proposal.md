## Why

Aportes e resgates em contas de investimento — bem como transferências entre contas bancárias — são registrados hoje como dois lançamentos independentes sem nenhum vínculo entre eles. Isso impede o usuário de saber, nas movimentações da conta bancária, para qual investimento foi o dinheiro (ou de qual investimento ele voltou), e dificulta o rastreamento de transferências internas.

## What Changes

- Novo campo `lancamento_vinculado` no modelo `Lancamento`: auto-FK nullable que liga dois lançamentos como par de uma mesma operação financeira.
- Ao setar o vínculo em um lado, o sistema seta automaticamente o vínculo reverso no outro (bidirecional, no `save()`).
- Validação: os dois lançamentos vinculados devem ter o mesmo valor absoluto — o sistema bloqueia o vínculo se os valores diferirem.
- Ao excluir um lançamento que possui par vinculado, o sistema avisa e oferece a opção de excluir o par junto.
- Campo de vínculo disponível no formulário de criação de lançamentos e no formulário de edição.
- Nova coluna "Contraparte" na visão consolidada, exibindo o nome da conta do lançamento vinculado quando presente.
- Visão patrimônio passa a exibir a conta bancária de origem/destino de cada aporte e resgate vinculados.

## Capabilities

### New Capabilities

- `lancamento-vinculado`: Vínculo bidirecional entre dois lançamentos que representam os dois lados de uma mesma operação financeira (aporte, resgate ou transferência entre contas).

### Modified Capabilities

- `lancamentos`: Novo campo `lancamento_vinculado`, nova regra de validação de valor igual entre o par, e novo comportamento de aviso ao excluir lançamento vinculado.
- `visualizacao`: Coluna "Contraparte" na visão consolidada e coluna de conta banco na visão patrimônio.

## Impact

- `lancamentos/models.py`: novo campo `lancamento_vinculado` com lógica de sincronização no `save()` e `delete()`.
- `lancamentos/forms.py`: campo `lancamento_vinculado` exposto no `LancamentoForm` com validação de valor.
- `lancamentos/views.py`: interceptação do `delete` para exibir aviso de par vinculado.
- `meses/services.py`: sem impacto direto — o campo é nullable e não afeta cálculos de saldo.
- `visualizacao/views.py` e templates: nova coluna na visão consolidada e na visão patrimônio.
- Migração de banco de dados necessária para o novo campo.
