# Delta for Contas

## ADDED Requirements

### Requirement: Tipos de conta suportados
O sistema SHALL suportar três tipos de conta — Cartão, Banco e Investimento — cada
um com campos próprios.

#### Scenario: Criar conta do tipo Cartão
- GIVEN o usuário está cadastrando uma nova conta do tipo Cartão
- WHEN ele informa Nome e Dia de vencimento da fatura
- THEN o sistema SHALL criar a conta com esses dois campos, sem campo de limite de crédito

#### Scenario: Criar conta do tipo Banco
- GIVEN o usuário está cadastrando uma nova conta do tipo Banco
- WHEN ele informa Nome, Saldo atual e Limite de cheque especial
- THEN o sistema SHALL criar a conta com esses três campos

#### Scenario: Criar conta do tipo Investimento
- GIVEN o usuário está cadastrando uma nova conta do tipo Investimento
- WHEN ele informa Nome e Saldo atual
- THEN o sistema SHALL criar a conta sem campos de limite ou vencimento

### Requirement: Saldo inicial obrigatório na criação de conta
O sistema SHALL exigir que o usuário informe o saldo atual ao criar uma conta dos
tipos Banco ou Investimento, usando esse valor como ponto de partida da conta. Esse
saldo SHALL ser herdado como saldo inicial do primeiro mês criado para a conta.

#### Scenario: Conta Banco criada com saldo já existente
- GIVEN o usuário já possui R$ 1.200,00 em conta corrente
- WHEN ele cadastra essa conta como tipo Banco e informa R$ 1.200,00
- THEN o sistema SHALL registrar R$ 1.200,00 como saldo inicial da conta
- AND esse valor SHALL ser usado como saldo de partida do primeiro mês dessa conta

### Requirement: Exclusão de conta com lançamentos associados
O sistema SHALL impedir a exclusão de uma conta que possua qualquer lançamento
associado, independentemente do status desse lançamento.

#### Scenario: Tentativa de excluir conta com lançamentos
- GIVEN uma conta possui ao menos um lançamento vinculado
- WHEN o usuário tenta excluir essa conta
- THEN o sistema SHALL bloquear a exclusão
- AND SHALL informar ao usuário o motivo do bloqueio

### Requirement: Alerta de limite negativo em conta Banco
O sistema SHALL alertar o usuário quando o saldo de uma conta Banco se aproximar do
limite negativo configurado ou o ultrapassar. O limite é uma referência informativa:
o sistema SHALL NOT bloquear nenhum lançamento por causa do limite — o lançamento é
sempre registrado, mesmo que o saldo fique mais negativo que o limite configurado.

#### Scenario: Saída ultrapassa o limite negativo
- GIVEN uma conta Banco com limite negativo de R$ 500,00 e saldo atual de -R$ 480,00
- WHEN o usuário registra uma saída de R$ 50,00
- THEN o sistema SHALL registrar o lançamento normalmente
- AND SHALL exibir um alerta informando que o limite foi ultrapassado

#### Scenario: Saldo se aproxima do limite negativo
- GIVEN uma conta Banco com limite negativo de R$ 500,00 e saldo atual de -R$ 450,00
- WHEN o saldo da conta é recalculado após um novo lançamento
- THEN o sistema SHALL exibir um alerta de proximidade do limite

### Requirement: Conta Investimento restrita a Aporte e Resgate
O sistema SHALL permitir, em contas do tipo Investimento, apenas lançamentos dos
tipos Aporte (entrada) ou Resgate (saída), sem campos de limite ou vencimento
associados à conta.

#### Scenario: Depósito em conta Investimento
- GIVEN uma conta do tipo Investimento já cadastrada
- WHEN o usuário registra um Aporte de R$ 300,00 nessa conta
- THEN o sistema SHALL tratar o lançamento como uma entrada que aumenta o saldo
  acumulado da conta

### Requirement: Saldo de conta Investimento tratado separadamente
O sistema SHALL calcular e exibir o saldo acumulado de uma conta Investimento de
forma independente do saldo consolidado mensal das contas Banco e Cartão.

#### Scenario: Saldo de Investimento não soma no saldo consolidado
- GIVEN uma conta Investimento com saldo acumulado de R$ 5.000,00
- WHEN o usuário consulta o saldo consolidado do mês de Banco e Cartão
- THEN o sistema SHALL NOT incluir o saldo da conta Investimento nesse total
