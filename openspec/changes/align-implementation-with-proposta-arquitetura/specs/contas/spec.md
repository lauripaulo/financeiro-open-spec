# Delta for Contas

## ADDED Requirements

### Requirement: Cadastro de contas no fluxo principal da aplicacao
O sistema SHALL oferecer, no fluxo principal da aplicacao (fora do Django Admin),
telas para criar, editar e excluir contas dos tipos Cartao, Banco e Investimento,
reutilizando as mesmas validacoes de dominio ja definidas para cada tipo.

#### Scenario: Usuario cria conta Banco pela aplicacao
- **WHEN** o usuario acessa a tela de contas e cadastra uma conta Banco com nome,
  saldo inicial e limite negativo
- **THEN** o sistema SHALL salvar a conta com os campos obrigatorios do tipo Banco

#### Scenario: Usuario edita uma conta existente
- **WHEN** o usuario altera os dados de uma conta existente na tela de contas
- **THEN** o sistema SHALL validar os campos conforme o tipo da conta antes de salvar

#### Scenario: Usuario tenta excluir conta com lancamentos
- **WHEN** o usuario tenta excluir uma conta que possui lancamentos associados
- **THEN** o sistema SHALL bloquear a exclusao
- **AND** SHALL exibir mensagem explicando o motivo do bloqueio
