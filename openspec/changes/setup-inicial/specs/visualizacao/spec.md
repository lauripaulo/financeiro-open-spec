# Delta for Visualização

## ADDED Requirements

### Requirement: Visão de conta
O sistema SHALL permitir visualizar os lançamentos do mês filtrados por uma única
conta, exibindo apenas os lançamentos pertencentes a essa conta.

#### Scenario: Usuário filtra por uma conta específica
- GIVEN um mês com lançamentos em duas contas diferentes
- WHEN o usuário seleciona a Visão de conta para a conta "Banco do Brasil"
- THEN o sistema SHALL exibir apenas os lançamentos dessa conta

### Requirement: Visão consolidada
O sistema SHALL permitir visualizar todos os lançamentos do mês das contas Banco e
Cartão, ordenados por data de vencimento, com uma coluna indicando a qual conta
cada lançamento pertence. Contas do tipo Investimento SHALL NOT aparecer na Visão
consolidada.

#### Scenario: Usuário consulta a visão consolidada do mês
- GIVEN um mês com lançamentos em uma conta Banco e uma conta Cartão
- WHEN o usuário acessa a Visão consolidada
- THEN o sistema SHALL listar todos os lançamentos dessas contas em ordem de data
  de vencimento
- AND cada linha SHALL indicar a conta correspondente

### Requirement: Visão de patrimônio (contas Investimento)
O sistema SHALL oferecer uma visão própria para contas do tipo Investimento,
separada da Visão consolidada, mostrando o saldo acumulado de cada conta e o
histórico de Aportes e Resgates.

#### Scenario: Usuário consulta o patrimônio acumulado
- GIVEN duas contas Investimento com Aportes e Resgates registrados
- WHEN o usuário acessa a Visão de patrimônio
- THEN o sistema SHALL exibir o saldo acumulado de cada conta Investimento
- AND SHALL exibir o histórico de Aportes e Resgates de cada uma

### Requirement: Navegação entre meses
O sistema SHALL oferecer um seletor de mês e ano, além de botões de navegação para o
mês anterior e o mês seguinte.

#### Scenario: Navegação para o mês anterior
- GIVEN o usuário está visualizando abril/2026
- WHEN ele clica no botão de mês anterior
- THEN o sistema SHALL exibir março/2026

### Requirement: Confirmação ao editar mês encerrado
O sistema SHALL solicitar confirmação do usuário antes de permitir a edição de um
lançamento em um mês já encerrado (mês passado).

#### Scenario: Usuário tenta editar um lançamento de mês passado
- GIVEN um lançamento em um mês já encerrado
- WHEN o usuário tenta editá-lo
- THEN o sistema SHALL perguntar "Você realmente quer editar um mês já encerrado?"
- AND SHALL só aplicar a edição após confirmação

### Requirement: Comparativo entre meses
O sistema SHALL oferecer uma tela comparativa entre dois meses, com o mês atual e o
mês anterior selecionados por padrão, permitindo ao usuário escolher outros meses
para comparar.

#### Scenario: Comparação padrão entre mês atual e anterior
- GIVEN o usuário acessa a tela comparativa pela primeira vez
- WHEN a tela carrega
- THEN o sistema SHALL exibir, por padrão, a comparação entre o mês atual e o mês anterior

### Requirement: Indicação de status e ações por lançamento
O sistema SHALL exibir, para cada lançamento na tela principal do mês, seu Status
(Previsto, Pendente ou Pago) e as ações disponíveis: marcar como Pago, Editar e
Excluir.

#### Scenario: Ação de pagar um lançamento Previsto
- GIVEN um lançamento com Status Previsto
- WHEN o usuário aciona a ação "Pagar" e informa a data de pagamento
- THEN o sistema SHALL alterar o Status para Pago
