## ADDED Requirements

### Requirement: Limite negativo informado como valor positivo
O campo `limite_negativo` de Conta Banco SHALL representar a magnitude positiva do limite de cheque especial. O sistema SHALL orientar o usuário a informar valor positivo e SHALL rejeitar valor negativo no cadastro ou edição de conta.

#### Scenario: Formulário orienta valor positivo
- **WHEN** o usuário acessa o formulário de conta Banco
- **THEN** o campo Limite negativo SHALL exibir orientação indicando que o valor deve ser informado como positivo

#### Scenario: Valor negativo é rejeitado
- **WHEN** o usuário envia o formulário de conta Banco com `limite_negativo` menor que zero
- **THEN** o sistema SHALL rejeitar a submissão com erro de validação no campo Limite negativo
- **AND** SHALL NOT salvar o valor negativo

#### Scenario: Valor positivo continua permitido
- **WHEN** o usuário envia o formulário de conta Banco com `limite_negativo` igual a `2000,00`
- **THEN** o sistema SHALL aceitar o valor como limite negativo de referência
- **AND** os alertas de saldo SHALL comparar o saldo contra `-2000,00`
