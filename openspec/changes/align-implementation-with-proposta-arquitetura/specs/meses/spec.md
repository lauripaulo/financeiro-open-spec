# Delta for Meses

## MODIFIED Requirements

### Requirement: Tratamento de lancamentos pendentes do mes anterior
Ao criar um novo mes, o sistema SHALL exibir os lancamentos com Status Pendente do
mes anterior e SHALL solicitar ao usuario que escolha, para cada um, entre mante-lo
no mes anterior ou transferi-lo para o novo mes. O fluxo de abertura do mes SHALL
preservar essas decisoes como parte obrigatoria da conclusao da abertura.

#### Scenario: Usuario transfere um lancamento pendente
- **GIVEN** um Gasto Fixo com Status Pendente no mes anterior
- **WHEN** o usuario, ao criar o novo mes, escolhe transferi-lo
- **THEN** o sistema SHALL mover esse lancamento para o novo mes, mantendo seu Status

#### Scenario: Usuario mantem um lancamento no mes anterior
- **GIVEN** um lancamento Pendente listado na abertura do novo mes
- **WHEN** o usuario escolhe manter no mes anterior
- **THEN** o sistema SHALL manter a competencia original sem mover o lancamento

## ADDED Requirements

### Requirement: Validacao de elegibilidade na transferencia de pendente
O sistema SHALL permitir transferencia apenas para lancamentos que sejam pendentes
do mes imediatamente anterior ao mes em abertura. O sistema SHALL bloquear tentativa
de transferencia de lancamentos fora desse criterio.

#### Scenario: Tentativa de transferir lancamento nao elegivel
- **WHEN** o usuario tenta transferir um lancamento que nao pertence ao mes anterior
  ou nao esta em status Pendente
- **THEN** o sistema SHALL rejeitar a operacao
- **AND** SHALL informar que apenas pendentes do mes anterior podem ser transferidos
