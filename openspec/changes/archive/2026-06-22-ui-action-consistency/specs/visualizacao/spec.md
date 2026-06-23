## MODIFIED Requirements

### Requirement: Indicacao de status e acoes por lancamento
O sistema SHALL exibir, para cada lancamento na tela principal do mes, seu Status
(Previsto, Pendente ou Pago) e as acoes disponiveis: marcar como Pago, Editar e
Excluir. A acao Excluir SHALL exigir confirmacao explicita do usuario antes de ser
executada.

#### Scenario: Acao de pagar um lancamento Previsto
- GIVEN um lancamento com Status Previsto
- WHEN o usuario aciona a acao "Pagar" e informa a data de pagamento
- THEN o sistema SHALL alterar o Status para Pago

#### Scenario: Exclusao de lancamento exige confirmacao
- GIVEN um lancamento listado na tela principal
- WHEN o usuario aciona "Excluir"
- THEN o sistema SHALL solicitar confirmacao explicita do usuario
- AND SHALL somente excluir o lancamento apos a confirmacao

## ADDED Requirements

### Requirement: Atualizacao da tela apos acoes que nao navegam
Quando uma acao do usuario (Pagar, Excluir, Transferir pendente, Manter pendente ou
Ajustar saldo) for concluida sem levar o usuario a uma nova URL, o sistema SHALL
atualizar a pagina atual para refletir o resultado da acao, e SHALL exibir uma
mensagem de confirmacao ou erro referente a essa acao apos a atualizacao.

#### Scenario: Tela e atualizada apos excluir um lancamento
- GIVEN um lancamento listado na tela principal
- WHEN o usuario confirma a exclusao desse lancamento
- THEN o sistema SHALL atualizar a tela e remover o lancamento da lista exibida
- AND SHALL exibir uma mensagem confirmando a exclusao

#### Scenario: Tela e atualizada apos marcar um lancamento como pago
- GIVEN um lancamento com Status Previsto ou Pendente
- WHEN o usuario aciona "Pagar" e informa a data de pagamento
- THEN o sistema SHALL atualizar a tela exibindo o lancamento com Status Pago

#### Scenario: Tela e atualizada apos transferir ou manter um pendente
- GIVEN um lancamento Pendente do mes anterior listado na abertura do novo mes
- WHEN o usuario aciona "Transferir" ou "Manter"
- THEN o sistema SHALL atualizar a tela refletindo a decisao tomada
- AND SHALL exibir uma mensagem confirmando o resultado

### Requirement: Acoes primarias exibidas como botoes
Links que representam uma acao primaria de criacao ou edicao (por exemplo "Novo
lancamento", "Nova compra parcelada" e "Editar") SHALL ser exibidos com a mesma
identidade visual dos botoes de formulario da aplicacao, e nao como links de texto
simples.

#### Scenario: Link de acao primaria exibido como botao
- WHEN o usuario acessa a tela principal do mes
- THEN os links "Novo lancamento", "Nova compra parcelada" e "Editar" SHALL ser
  exibidos com aparencia de botao
