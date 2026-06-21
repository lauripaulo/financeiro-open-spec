## Why

Hoje todo valor monetário (saldo de conta, limite negativo, valor de lançamento, valor de compra parcelada, saldo inicial do mês) é exibido com a representação padrão de `Decimal` do Python (ex: `R$ 256432.11`, ponto como separador decimal, sem separador de milhar) e digitado em campos `<input type="number">` sem nenhuma máscara. Isso não corresponde à convenção brasileira de moeda (`R$ 256.432,11`), dificultando a leitura de valores grandes e a digitação consistente.

## What Changes

- Todos os valores monetários exibidos em tela (telas de contas, visão consolidada, patrimônio, comparativo) passam a ser formatados no padrão `R$ 1.234,56` (separador de milhar `.`, separador decimal `,`, sempre 2 casas decimais).
- Todos os campos de entrada de valor monetário (saldo atual, limite negativo, valor de lançamento, valor de compra parcelada) passam a usar uma máscara que formata o número digitado em tempo real no mesmo padrão (`1.234,56`), com o prefixo "R$" exibido ao lado do campo.
- O contrato de dados enviado ao servidor pelos formulários permanece o mesmo (decimal simples, ex: `1234.56`) — a máscara é uma camada de apresentação, sem mudança de validação ou de armazenamento.

## Capabilities

### New Capabilities
- `formatacao-monetaria`: regras de formatação de exibição e de máscara de entrada para todo valor monetário do sistema, no padrão brasileiro (R$, separador de milhar `.`, separador decimal `,`, 2 casas decimais).

### Modified Capabilities
(nenhuma — os specs existentes de `contas`, `lancamentos`, `meses`, `parcelas` e `visualizacao` definem regras de negócio sobre os valores, não seu formato de exibição/entrada; nenhum requisito existente muda.)

## Impact

- Templates de exibição: `templates/visualizacao/comparativo.html`, `templates/visualizacao/consolidada.html`, `templates/visualizacao/patrimonio.html`, `templates/contas/lista.html`.
- Formulários: `contas/forms.py` (`ContaForm`), `lancamentos/forms.py` (`LancamentoForm`, `CompraParceladaForm`).
- Novo filtro de template e novo widget de formulário (apresentação apenas, sem mudança de schema/model).
- Novo arquivo JS estático e ajuste de configuração de arquivos estáticos (`STATICFILES_DIRS`), já que o projeto ainda não serve nenhum asset estático.
- Sem impacto em models, migrations ou contrato de API/POST dos formulários.
