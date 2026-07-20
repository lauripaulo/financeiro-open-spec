# Visao Planejamento

## Purpose

Definir os requisitos da tela de planejamento financeiro que exibe saldo real, saldo projetado e resumo de faturas por tipo de conta, permitindo ao usuário entender sua posição financeira atual e futura.

## ADDED Requirements

### Requirement: Tela de planejamento acessível pela navbar

O sistema SHALL disponibilizar uma tela de planejamento em `/planejamento/` com link direto na navbar principal, ao lado das outras visões (Consolidada, Patrimônio, Comparativo).

#### Scenario: Usuário acessa tela de planejamento

- WHEN o usuário clica em "Planejamento" na navbar
- THEN o sistema SHALL exibir a tela de planejamento com a data de hoje como referência padrão

### Requirement: Date picker de data de referência

O sistema SHALL exibir um seletor de data na tela de planejamento. O valor padrão SHALL ser a data de hoje. Ao alterar a data, os saldos de contas Banco SHALL ser recalculados com base na nova data. Contas Cartão e Investimento SHALL permanecer inalteradas pela data de referência.

#### Scenario: Usuário seleciona data futura

- GIVEN a tela de planejamento está aberta com data de hoje
- WHEN o usuário seleciona uma data futura em mês já aberto
- THEN o sistema SHALL recalcular saldo real e projetado das contas Banco para essa data

#### Scenario: Usuário seleciona data em mês não aberto

- GIVEN a tela de planejamento está aberta
- WHEN o usuário seleciona uma data cujo mês não está em MesAberto
- THEN o sistema SHALL usar o último mês aberto como proxy
- AND SHALL exibir aviso informando que o mês da data selecionada não está aberto

### Requirement: Saldo Real de contas Banco

Para cada conta do tipo Banco, o sistema SHALL exibir o Saldo Real calculado como:
- Âncora: `SaldoMensalConta` do mês da data de referência (fallback: `conta.saldo_atual`)
- Soma: apenas lançamentos com `data_pagamento` preenchida e `data_pagamento ≤ data_referência`, restritos ao `competencia_mes` da data de referência

O sistema SHALL exibir o total consolidado de Saldo Real para todas as contas Banco.

#### Scenario: Saldo Real considera apenas pagos

- GIVEN uma conta Banco com saldo inicial R$ 1.000,00 no mês atual
- AND um lançamento PAGO de +R$ 3.000,00 com data_pagamento = hoje
- AND um lançamento PREVISTO de -R$ 500,00 com data_vencimento = amanhã
- WHEN o usuário visualiza o Saldo Real para a data de hoje
- THEN o sistema SHALL exibir R$ 4.000,00 (inicial + pago)
- AND SHALL NOT incluir o lançamento previsto de -R$ 500,00

### Requirement: Saldo Projetado de contas Banco

Para cada conta do tipo Banco, o sistema SHALL exibir o Saldo Projetado calculado como:
- Âncora: mesma do Saldo Real
- Soma: lançamentos com `data_pagamento ≤ data_referência` OU lançamentos com `data_pagamento` nulo e `data_vencimento ≤ data_referência`, restritos ao `competencia_mes` da data de referência

O sistema SHALL exibir o total consolidado de Saldo Projetado para todas as contas Banco.

#### Scenario: Saldo Projetado inclui previstos até a data

- GIVEN uma conta Banco com saldo inicial R$ 1.000,00 no mês atual
- AND um lançamento PAGO de +R$ 3.000,00 com data_pagamento = hoje
- AND um lançamento PREVISTO de -R$ 500,00 com data_vencimento = amanhã
- AND um lançamento PREVISTO de -R$ 200,00 com data_vencimento = dia 30 do mês
- WHEN o usuário visualiza o Saldo Projetado para a data de amanhã
- THEN o sistema SHALL exibir R$ 3.500,00 (inicial + pago + previsto de amanhã)
- AND SHALL NOT incluir o lançamento de dia 30

#### Scenario: Saldo Real e Projetado diferem quando há previstos

- GIVEN uma conta Banco com lançamentos pagos e lançamentos previstos para a mesma data de referência
- WHEN o usuário visualiza a tela de planejamento
- THEN Saldo Real SHALL ser menor ou igual ao Saldo Projetado (para conta com entradas) ou maior ou igual (para conta com saídas)
- AND ambos SHALL ser exibidos lado a lado na mesma linha da conta

### Requirement: Total de gastos de cartão por mês (Fatura)

Para cada conta do tipo Cartão, o sistema SHALL exibir colunas com o total de saídas por mês, cobrindo o mês atual e até 3 meses futuros abertos (máximo 4 colunas). O total SHALL incluir todos os lançamentos de saída independente de status (pagos, pendentes ou previstos).

#### Scenario: Exibição de fatura do mês atual

- GIVEN uma conta Cartão com gastos de R$ 850,00 no mês atual (pagos e previstos)
- WHEN o usuário acessa a tela de planejamento
- THEN a coluna do mês atual SHALL exibir R$ 850,00 para essa conta

#### Scenario: Meses futuros sem lançamentos exibem valor zero ou traço

- GIVEN um mês futuro aberto sem lançamentos para uma conta Cartão
- WHEN o usuário acessa a tela de planejamento
- THEN a coluna desse mês SHALL exibir R$ 0,00 ou "—"

#### Scenario: Máximo de 4 colunas para cartão

- GIVEN 6 meses abertos no sistema
- WHEN o usuário acessa a tela de planejamento
- THEN o sistema SHALL exibir apenas 4 colunas (mês atual + 3 seguintes)

### Requirement: Saldo Real de contas Investimento

Para cada conta do tipo Investimento, o sistema SHALL exibir o Saldo Real acumulado calculado como `saldo_atual + aportes - resgates`. O sistema SHALL exibir o total consolidado para todas as contas Investimento. A data de referência SHALL NOT afetar o saldo de investimentos.

#### Scenario: Investimento exibe apenas saldo real

- GIVEN uma conta Investimento com saldo_atual R$ 5.000,00 e aporte de R$ 1.000,00
- WHEN o usuário acessa a tela de planejamento
- THEN o sistema SHALL exibir R$ 6.000,00 como saldo da conta
- AND SHALL NOT exibir coluna de "saldo projetado" para investimentos

### Requirement: Comportamento com nenhum mês aberto

Se nenhum mês estiver aberto no sistema, o sistema SHALL exibir mensagem orientando o usuário a criar o primeiro mês antes de usar a tela de planejamento.

#### Scenario: Sem meses abertos

- GIVEN nenhum MesAberto existe no sistema
- WHEN o usuário acessa `/planejamento/`
- THEN o sistema SHALL exibir mensagem informando que nenhum mês está aberto
- AND SHALL orientar o usuário a criar o primeiro mês
