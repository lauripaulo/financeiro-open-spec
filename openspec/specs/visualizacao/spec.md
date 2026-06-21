# Visualizacao

## Purpose
Definir as visoes de consulta mensal, historico e acoes de interacao do usuario.

## Requirements

### Requirement: Visao de conta
O sistema SHALL permitir visualizar os lancamentos do mes filtrados por uma unica
conta, exibindo apenas os lancamentos pertencentes a essa conta. Quando essa visao
estiver ativa, os totais exibidos (entradas, saidas e saldo) SHALL refletir apenas
o escopo da conta selecionada.

#### Scenario: Usuario filtra por uma conta especifica
- GIVEN um mes com lancamentos em duas contas diferentes
- WHEN o usuario seleciona a Visao de conta para a conta "Banco do Brasil"
- THEN o sistema SHALL exibir apenas os lancamentos dessa conta

#### Scenario: Totais da visao de conta respeitam a conta selecionada
- GIVEN o usuario esta com filtro de uma conta especifica ativo
- WHEN a tela calcula entradas, saidas e saldo
- THEN o sistema SHALL considerar somente lancamentos da conta selecionada

### Requirement: Identificacao explicita do escopo de saldo na tela principal
O sistema SHALL indicar claramente se o saldo exibido na tela principal representa
o consolidado de Banco+Cartao ou o saldo de uma conta especifica filtrada.

#### Scenario: Tela com conta filtrada informa escopo
- WHEN o usuario aplica filtro por conta na tela principal
- THEN o sistema SHALL exibir rotulo indicando que o saldo mostrado e da conta filtrada

#### Scenario: Tela sem filtro informa consolidado
- WHEN o usuario remove o filtro de conta na tela principal
- THEN o sistema SHALL exibir rotulo indicando que o saldo mostrado e consolidado

### Requirement: Visao consolidada
O sistema SHALL permitir visualizar todos os lancamentos do mes das contas Banco e
Cartao, ordenados por data de vencimento, com uma coluna indicando a qual conta
cada lancamento pertence. Contas do tipo Investimento SHALL NOT aparecer na Visao
consolidada.

#### Scenario: Usuario consulta a visao consolidada do mes
- GIVEN um mes com lancamentos em uma conta Banco e uma conta Cartao
- WHEN o usuario acessa a Visao consolidada
- THEN o sistema SHALL listar todos os lancamentos dessas contas em ordem de data
  de vencimento
- AND cada linha SHALL indicar a conta correspondente

### Requirement: Visao de patrimonio (contas Investimento)
O sistema SHALL oferecer uma visao propria para contas do tipo Investimento,
separada da Visao consolidada, mostrando o saldo acumulado de cada conta e o
historico de Aportes e Resgates.

#### Scenario: Usuario consulta o patrimonio acumulado
- GIVEN duas contas Investimento com Aportes e Resgates registrados
- WHEN o usuario acessa a Visao de patrimonio
- THEN o sistema SHALL exibir o saldo acumulado de cada conta Investimento
- AND SHALL exibir o historico de Aportes e Resgates de cada uma

### Requirement: Navegacao entre meses
O sistema SHALL oferecer um seletor de mes e ano, alem de botoes de navegacao para o
mes anterior e o mes seguinte.

#### Scenario: Navegacao para o mes anterior
- GIVEN o usuario esta visualizando abril/2026
- WHEN ele clica no botao de mes anterior
- THEN o sistema SHALL exibir marco/2026

### Requirement: Confirmacao ao editar mes encerrado
O sistema SHALL solicitar confirmacao do usuario antes de permitir a edicao de um
lancamento em um mes ja encerrado (mes passado).

#### Scenario: Usuario tenta editar um lancamento de mes passado
- GIVEN um lancamento em um mes ja encerrado
- WHEN o usuario tenta edita-lo
- THEN o sistema SHALL perguntar "Voce realmente quer editar um mes ja encerrado?"
- AND SHALL so aplicar a edicao apos confirmacao

### Requirement: Comparativo entre meses
O sistema SHALL oferecer uma tela comparativa entre dois meses, com o mes atual e o
mes anterior selecionados por padrao, permitindo ao usuario escolher outros meses
para comparar.

#### Scenario: Comparacao padrao entre mes atual e anterior
- GIVEN o usuario acessa a tela comparativa pela primeira vez
- WHEN a tela carrega
- THEN o sistema SHALL exibir, por padrao, a comparacao entre o mes atual e o mes anterior

### Requirement: Indicacao de status e acoes por lancamento
O sistema SHALL exibir, para cada lancamento na tela principal do mes, seu Status
(Previsto, Pendente ou Pago) e as acoes disponiveis: marcar como Pago, Editar e
Excluir.

#### Scenario: Acao de pagar um lancamento Previsto
- GIVEN um lancamento com Status Previsto
- WHEN o usuario aciona a acao "Pagar" e informa a data de pagamento
- THEN o sistema SHALL alterar o Status para Pago
