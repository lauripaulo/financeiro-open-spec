# Delta for Visualizacao

## MODIFIED Requirements

### Requirement: Visao de conta
O sistema SHALL permitir visualizar os lancamentos do mes filtrados por uma unica
conta, exibindo apenas os lancamentos pertencentes a essa conta. Quando essa visao
estiver ativa, os totais exibidos (entradas, saidas e saldo) SHALL refletir apenas
o escopo da conta selecionada.

#### Scenario: Usuario filtra por uma conta especifica
- **GIVEN** um mes com lancamentos em duas contas diferentes
- **WHEN** o usuario seleciona a Visao de conta para a conta "Banco do Brasil"
- **THEN** o sistema SHALL exibir apenas os lancamentos dessa conta

#### Scenario: Totais da visao de conta respeitam a conta selecionada
- **GIVEN** o usuario esta com filtro de uma conta especifica ativo
- **WHEN** a tela calcula entradas, saidas e saldo
- **THEN** o sistema SHALL considerar somente lancamentos da conta selecionada

## ADDED Requirements

### Requirement: Identificacao explicita do escopo de saldo na tela principal
O sistema SHALL indicar claramente se o saldo exibido na tela principal representa
o consolidado de Banco+Cartao ou o saldo de uma conta especifica filtrada.

#### Scenario: Tela com conta filtrada informa escopo
- **WHEN** o usuario aplica filtro por conta na tela principal
- **THEN** o sistema SHALL exibir rotulo indicando que o saldo mostrado e da conta filtrada

#### Scenario: Tela sem filtro informa consolidado
- **WHEN** o usuario remove o filtro de conta na tela principal
- **THEN** o sistema SHALL exibir rotulo indicando que o saldo mostrado e consolidado
