# Contas

## Purpose
Definir regras de tipos de conta, validacoes e comportamento de saldo/limite.

## Requirements

### Requirement: Tipos de conta suportados
O sistema SHALL suportar tres tipos de conta - Cartao, Banco e Investimento - cada
um com campos proprios.

#### Scenario: Criar conta do tipo Cartao
- GIVEN o usuario esta cadastrando uma nova conta do tipo Cartao
- WHEN ele informa Nome e Dia de vencimento da fatura
- THEN o sistema SHALL criar a conta com esses dois campos, sem campo de limite de credito

#### Scenario: Criar conta do tipo Banco
- GIVEN o usuario esta cadastrando uma nova conta do tipo Banco
- WHEN ele informa Nome, Saldo atual e Limite de cheque especial
- THEN o sistema SHALL criar a conta com esses tres campos

#### Scenario: Criar conta do tipo Investimento
- GIVEN o usuario esta cadastrando uma nova conta do tipo Investimento
- WHEN ele informa Nome e Saldo atual
- THEN o sistema SHALL criar a conta sem campos de limite ou vencimento

### Requirement: Saldo inicial obrigatorio na criacao de conta
O sistema SHALL exigir que o usuario informe o saldo atual ao criar uma conta dos
tipos Banco ou Investimento, usando esse valor como ponto de partida da conta. Esse
saldo SHALL ser herdado como saldo inicial do primeiro mes criado para a conta.

#### Scenario: Conta Banco criada com saldo ja existente
- GIVEN o usuario ja possui R$ 1.200,00 em conta corrente
- WHEN ele cadastra essa conta como tipo Banco e informa R$ 1.200,00
- THEN o sistema SHALL registrar R$ 1.200,00 como saldo inicial da conta
- AND esse valor SHALL ser usado como saldo de partida do primeiro mes dessa conta

### Requirement: Exclusao de conta com lancamentos associados
O sistema SHALL impedir a exclusao de uma conta que possua qualquer lancamento
associado, independentemente do status desse lancamento.

#### Scenario: Tentativa de excluir conta com lancamentos
- GIVEN uma conta possui ao menos um lancamento vinculado
- WHEN o usuario tenta excluir essa conta
- THEN o sistema SHALL bloquear a exclusao
- AND SHALL informar ao usuario o motivo do bloqueio

### Requirement: Alerta de limite negativo em conta Banco
O sistema SHALL alertar o usuario quando o saldo de uma conta Banco se aproximar do
limite negativo configurado ou o ultrapassar. O limite e uma referencia informativa:
o sistema SHALL NOT bloquear nenhum lancamento por causa do limite - o lancamento e
sempre registrado, mesmo que o saldo fique mais negativo que o limite configurado.

#### Scenario: Saida ultrapassa o limite negativo
- GIVEN uma conta Banco com limite negativo de R$ 500,00 e saldo atual de -R$ 480,00
- WHEN o usuario registra uma saida de R$ 50,00
- THEN o sistema SHALL registrar o lancamento normalmente
- AND SHALL exibir um alerta informando que o limite foi ultrapassado

#### Scenario: Saldo se aproxima do limite negativo
- GIVEN uma conta Banco com limite negativo de R$ 500,00 e saldo atual de -R$ 450,00
- WHEN o saldo da conta e recalculado apos um novo lancamento
- THEN o sistema SHALL exibir um alerta de proximidade do limite

### Requirement: Conta Investimento restrita a Aporte e Resgate
O sistema SHALL permitir, em contas do tipo Investimento, apenas lancamentos dos
tipos Aporte (entrada) ou Resgate (saida), sem campos de limite ou vencimento
associados a conta.

#### Scenario: Deposito em conta Investimento
- GIVEN uma conta do tipo Investimento ja cadastrada
- WHEN o usuario registra um Aporte de R$ 300,00 nessa conta
- THEN o sistema SHALL tratar o lancamento como uma entrada que aumenta o saldo
  acumulado da conta

### Requirement: Saldo de conta Investimento tratado separadamente
O sistema SHALL calcular e exibir o saldo acumulado de uma conta Investimento de
forma independente do saldo consolidado mensal das contas Banco e Cartao.

#### Scenario: Saldo de Investimento nao soma no saldo consolidado
- GIVEN uma conta Investimento com saldo acumulado de R$ 5.000,00
- WHEN o usuario consulta o saldo consolidado do mes de Banco e Cartao
- THEN o sistema SHALL NOT incluir o saldo da conta Investimento nesse total
