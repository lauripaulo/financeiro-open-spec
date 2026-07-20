# Visao Planejamento

## Purpose

Definir os requisitos da tela de planejamento financeiro que exibe saldo real, saldo projetado e resumo de faturas por tipo de conta, permitindo ao usuario entender sua posicao financeira atual e futura.

## Requirements

### Requirement: Tela de planejamento acessivel pela navbar

O sistema SHALL disponibilizar uma tela de planejamento em `/planejamento/` com link direto na navbar principal, ao lado das outras visoes (Consolidada, Patrimonio, Comparativo).

#### Scenario: Usuario acessa tela de planejamento

- WHEN o usuario clica em "Planejamento" na navbar
- THEN o sistema SHALL exibir a tela de planejamento com a data de hoje como referencia padrao

### Requirement: Date picker de data de referencia

O sistema SHALL exibir um seletor de data na tela de planejamento. O valor padrao SHALL ser a data de hoje. Ao alterar a data, os saldos de contas Banco SHALL ser recalculados com base na nova data. Contas Cartao e Investimento SHALL permanecer inalteradas pela data de referencia.

#### Scenario: Usuario seleciona data futura

- GIVEN a tela de planejamento esta aberta com data de hoje
- WHEN o usuario seleciona uma data futura em mes ja aberto
- THEN o sistema SHALL recalcular saldo real e projetado das contas Banco para essa data

#### Scenario: Usuario seleciona data em mes nao aberto

- GIVEN a tela de planejamento esta aberta
- WHEN o usuario seleciona uma data cujo mes nao esta em MesAberto
- THEN o sistema SHALL usar o ultimo mes aberto como proxy
- AND SHALL exibir aviso informando que o mes da data selecionada nao esta aberto

### Requirement: Saldo Real de contas Banco

Para cada conta do tipo Banco, o sistema SHALL exibir o Saldo Real calculado como:
- Ancora: `SaldoMensalConta` do mes da data de referencia (fallback: `conta.saldo_atual`)
- Soma: apenas lancamentos com `data_pagamento` preenchida e `data_pagamento <= data_referencia`, restritos ao `competencia_mes` da data de referencia

O sistema SHALL exibir o total consolidado de Saldo Real para todas as contas Banco.

#### Scenario: Saldo Real considera apenas pagos

- GIVEN uma conta Banco com saldo inicial R$ 1.000,00 no mes atual
- AND um lancamento PAGO de +R$ 3.000,00 com data_pagamento = hoje
- AND um lancamento PREVISTO de -R$ 500,00 com data_vencimento = amanha
- WHEN o usuario visualiza o Saldo Real para a data de hoje
- THEN o sistema SHALL exibir R$ 4.000,00 (inicial + pago)
- AND SHALL NOT incluir o lancamento previsto de -R$ 500,00

### Requirement: Saldo Projetado de contas Banco

Para cada conta do tipo Banco, o sistema SHALL exibir o Saldo Projetado calculado como:
- Ancora: mesma do Saldo Real
- Soma: lancamentos com `data_pagamento <= data_referencia` OU lancamentos com `data_pagamento` nulo e `data_vencimento <= data_referencia`, restritos ao `competencia_mes` da data de referencia

O sistema SHALL exibir o total consolidado de Saldo Projetado para todas as contas Banco.

#### Scenario: Saldo Projetado inclui previstos ate a data

- GIVEN uma conta Banco com saldo inicial R$ 1.000,00 no mes atual
- AND um lancamento PAGO de +R$ 3.000,00 com data_pagamento = hoje
- AND um lancamento PREVISTO de -R$ 500,00 com data_vencimento = amanha
- AND um lancamento PREVISTO de -R$ 200,00 com data_vencimento = dia 30 do mes
- WHEN o usuario visualiza o Saldo Projetado para a data de amanha
- THEN o sistema SHALL exibir R$ 3.500,00 (inicial + pago + previsto de amanha)
- AND SHALL NOT incluir o lancamento de dia 30

#### Scenario: Saldo Real e Projetado diferem quando ha previstos

- GIVEN uma conta Banco com lancamentos pagos e lancamentos previstos para a mesma data de referencia
- WHEN o usuario visualiza a tela de planejamento
- THEN Saldo Real SHALL ser menor ou igual ao Saldo Projetado (para conta com entradas) ou maior ou igual (para conta com saidas)
- AND ambos SHALL ser exibidos lado a lado na mesma linha da conta

### Requirement: Total de gastos de cartao por mes (Fatura)

Para cada conta do tipo Cartao, o sistema SHALL exibir colunas com o total de saidas por mes, cobrindo o mes atual e ate 3 meses futuros abertos (maximo 4 colunas). O total SHALL incluir todos os lancamentos de saida independente de status (pagos, pendentes ou previstos).

#### Scenario: Exibicao de fatura do mes atual

- GIVEN uma conta Cartao com gastos de R$ 850,00 no mes atual (pagos e previstos)
- WHEN o usuario acessa a tela de planejamento
- THEN a coluna do mes atual SHALL exibir R$ 850,00 para essa conta

#### Scenario: Meses futuros sem lancamentos exibem valor zero ou traco

- GIVEN um mes futuro aberto sem lancamentos para uma conta Cartao
- WHEN o usuario acessa a tela de planejamento
- THEN a coluna desse mes SHALL exibir R$ 0,00 ou "-"

#### Scenario: Maximo de 4 colunas para cartao

- GIVEN 6 meses abertos no sistema
- WHEN o usuario acessa a tela de planejamento
- THEN o sistema SHALL exibir apenas 4 colunas (mes atual + 3 seguintes)

### Requirement: Saldo Real de contas Investimento

Para cada conta do tipo Investimento, o sistema SHALL exibir o Saldo Real acumulado calculado como `saldo_atual + aportes - resgates`. O sistema SHALL exibir o total consolidado para todas as contas Investimento. A data de referencia SHALL NOT afetar o saldo de investimentos.

#### Scenario: Investimento exibe apenas saldo real

- GIVEN uma conta Investimento com saldo_atual R$ 5.000,00 e aporte de R$ 1.000,00
- WHEN o usuario acessa a tela de planejamento
- THEN o sistema SHALL exibir R$ 6.000,00 como saldo da conta
- AND SHALL NOT exibir coluna de "saldo projetado" para investimentos

### Requirement: Comportamento com nenhum mes aberto

Se nenhum mes estiver aberto no sistema, o sistema SHALL exibir mensagem orientando o usuario a criar o primeiro mes antes de usar a tela de planejamento.

#### Scenario: Sem meses abertos

- GIVEN nenhum MesAberto existe no sistema
- WHEN o usuario acessa `/planejamento/`
- THEN o sistema SHALL exibir mensagem informando que nenhum mes esta aberto
- AND SHALL orientar o usuario a criar o primeiro mes
