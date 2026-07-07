## ADDED Requirements

### Requirement: Criacao de transferencia entre contas operacionais
O sistema SHALL permitir registrar uma transferencia de valor entre duas contas do tipo
BANCO ou CARTAO por meio de um formulario dedicado. O formulario SHALL criar
atomicamente um par de lancamentos vinculados: um `TRANSFERENCIA_ENVIADA` na conta
origem (saida) e um `TRANSFERENCIA_RECEBIDA` na conta destino (entrada), ambos com o
mesmo valor, descricao e data de vencimento. Contas do tipo INVESTIMENTO SHALL NOT
ser aceitas nesse fluxo.

#### Scenario: Transferencia valida cria par vinculado
- **WHEN** o usuario preenche o formulario de transferencia com conta_origem (BANCO),
  conta_destino (BANCO), valor, data_vencimento e descricao e confirma
- **THEN** o sistema SHALL criar um lancamento `TRANSFERENCIA_ENVIADA` na conta_origem
- **AND** SHALL criar um lancamento `TRANSFERENCIA_RECEBIDA` na conta_destino
- **AND** os dois lancamentos SHALL estar vinculados via `lancamento_vinculado`
- **AND** ambos SHALL ter o mesmo valor, descricao e data_vencimento

#### Scenario: Conta INVESTIMENTO e recusada como origem ou destino
- **WHEN** o usuario tenta selecionar uma conta do tipo INVESTIMENTO como origem ou destino
- **THEN** o sistema SHALL nao disponibilizar essa conta no seletor do formulario

#### Scenario: Conta origem e destino nao podem ser a mesma
- **WHEN** o usuario informa a mesma conta em conta_origem e conta_destino
- **THEN** o sistema SHALL rejeitar a submissao com erro de validacao

#### Scenario: Transferencia bem-sucedida exibe mensagem de confirmacao
- **WHEN** a transferencia e criada com sucesso
- **THEN** o sistema SHALL exibir uma mensagem de sucesso identificando a transferencia criada
- **AND** SHALL redirecionar para a visao consolidada do mes

### Requirement: Transferencia nao e propagada entre meses
O sistema SHALL NOT propagar lancamentos do tipo `TRANSFERENCIA_ENVIADA` ou
`TRANSFERENCIA_RECEBIDA` na abertura de um novo mes. Transferencias sao operacoes
pontuais, sem recorrencia automatica.

#### Scenario: Abertura de novo mes nao duplica transferencias
- **GIVEN** um lancamento `TRANSFERENCIA_ENVIADA` no mes atual
- **WHEN** um novo mes e criado pelo usuario
- **THEN** o sistema SHALL NOT gerar copia desse lancamento no novo mes
