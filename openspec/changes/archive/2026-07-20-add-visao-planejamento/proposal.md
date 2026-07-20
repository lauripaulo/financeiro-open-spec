## Why

Hoje é impossível saber o saldo atual de uma conta corrente ou projetar o saldo em uma data futura, pois o sistema é exclusivamente orientado a competência mensal. O campo `Conta.saldo_atual` é uma semente histórica que fica obsoleta após o primeiro mês aberto. Isso impede planejamento financeiro real: o usuário não consegue responder "quanto tenho no banco hoje?" ou "vou ter saldo suficiente no dia 15 do próximo mês?".

## What Changes

- Nova tela de **Planejamento Financeiro** acessível pela navbar principal em `/planejamento/`
- Para contas **Banco**: dois saldos por data de referência selecionável
  - **Saldo Real**: saldo inicial herdado do mês + apenas lançamentos pagos (`data_pagamento`) até a data
  - **Saldo Projetado**: saldo inicial herdado + todos os lançamentos com vencimento até a data (pagos ou planejados)
- Para contas **Cartão**: total de gastos por fatura (mês atual + até 3 meses futuros abertos), incluindo pagos e não pagos
- Para contas **Investimento**: saldo real acumulado (reaproveitando `saldo_investimento` já existente)
- Novas funções de serviço puras em `meses/services.py`
- **Nenhuma mudança de modelo de dados — sem migrations**

## Capabilities

### New Capabilities

- `visao-planejamento`: Tela de planejamento financeiro com saldo real e projetado por data de referência para contas bancárias, resumo de faturas por mês (até 4 meses) para cartões, e saldo real para investimentos. Inclui date picker para seleção da data de referência. Apenas meses já abertos no sistema são considerados.

### Modified Capabilities

*(Nenhuma capability existente tem requisitos alterados.)*

## Impact

- `meses/services.py`: 3 novas funções (`saldo_real_em_data`, `saldo_projetado_em_data`, `total_gastos_cartao_por_mes`)
- `visualizacao/services.py`: novo dataclass `ResumoPlajamento` e função `planejamento_financeiro`
- `visualizacao/views.py`: nova view `visao_planejamento`
- `visualizacao/urls.py`: novo path `planejamento/`
- `templates/base.html`: novo link "Planejamento" na navbar
- `templates/visualizacao/planejamento.html`: novo template
- `meses/tests.py` e `visualizacao/tests.py`: novos casos de teste
