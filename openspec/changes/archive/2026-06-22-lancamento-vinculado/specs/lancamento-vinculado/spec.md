## ADDED Requirements

### Requirement: Vínculo bidirecional entre lançamentos
O sistema SHALL permitir vincular dois lançamentos como par de uma mesma operação
financeira por meio do campo `lancamento_vinculado`. O vínculo SHALL ser bidirecional:
ao definir `A.lancamento_vinculado = B`, o sistema SHALL automaticamente definir
`B.lancamento_vinculado = A`.

#### Scenario: Setar vínculo em um lado sincroniza o lado oposto
- **WHEN** o usuário define `lancamento_vinculado` de A como B
- **THEN** o sistema SHALL definir `lancamento_vinculado` de B como A automaticamente

#### Scenario: Trocar vínculo limpa o par anterior e liga o novo
- **GIVEN** `A.lancamento_vinculado = B`
- **WHEN** o usuário redefine `A.lancamento_vinculado = C`
- **THEN** o sistema SHALL limpar `B.lancamento_vinculado`
- **AND** SHALL definir `C.lancamento_vinculado = A`

#### Scenario: Remover vínculo limpa os dois lados
- **GIVEN** `A.lancamento_vinculado = B`
- **WHEN** o usuário remove o vínculo de A (seta para nulo)
- **THEN** o sistema SHALL também limpar `B.lancamento_vinculado`

### Requirement: Valores absolutos iguais obrigatórios para o par
O sistema SHALL bloquear o vínculo entre dois lançamentos quando seus valores absolutos
diferirem, exibindo mensagem de erro clara ao usuário.

#### Scenario: Vínculo bloqueado quando valores absolutos diferem
- **GIVEN** lançamento A com valor R$ 500,00 e lançamento B com valor R$ 400,00
- **WHEN** o usuário tenta definir `A.lancamento_vinculado = B`
- **THEN** o sistema SHALL rejeitar a operação com mensagem de erro informando a divergência de valores

#### Scenario: Vínculo permitido quando valores absolutos são iguais
- **GIVEN** lançamento A (tipo APORTE) com valor R$ 500,00 e lançamento B com valor R$ 500,00
- **WHEN** o usuário define `A.lancamento_vinculado = B`
- **THEN** o sistema SHALL aceitar o vínculo e sincronizar o lado reverso

### Requirement: Aviso ao excluir lançamento vinculado
O sistema SHALL avisar o usuário ao tentar excluir um lançamento que possua par
vinculado, oferecendo a opção de excluir somente este lançamento ou excluir os dois
lançamentos do par.

#### Scenario: Aviso exibido ao excluir lançamento com par
- **GIVEN** lançamento A com `lancamento_vinculado = B`
- **WHEN** o usuário solicita a exclusão de A
- **THEN** o sistema SHALL exibir aviso identificando que A possui par vinculado
- **AND** SHALL oferecer as opções: excluir somente A, ou excluir A e B

#### Scenario: Excluir somente um lado limpa o vínculo do sobrevivente
- **GIVEN** lançamento A vinculado a lançamento B
- **WHEN** o usuário confirma excluir somente A
- **THEN** o sistema SHALL excluir A
- **AND** `B.lancamento_vinculado` SHALL ser nulo após a exclusão

#### Scenario: Excluir os dois remove o par completo
- **GIVEN** lançamento A vinculado a lançamento B
- **WHEN** o usuário confirma excluir A e B
- **THEN** o sistema SHALL excluir ambos os lançamentos

### Requirement: Campo de vínculo disponível na criação e edição de lançamentos
O sistema SHALL disponibilizar o campo `lancamento_vinculado` como opcional no
formulário de criação de um novo lançamento e no formulário de edição de lançamento
existente.

#### Scenario: Campo disponível ao criar novo lançamento
- **WHEN** o usuário abre o formulário de novo lançamento
- **THEN** o sistema SHALL exibir o campo de lançamento vinculado como opcional

#### Scenario: Campo disponível ao editar lançamento existente
- **WHEN** o usuário abre o formulário de edição de um lançamento
- **THEN** o sistema SHALL exibir o campo com o valor atual do vínculo (ou vazio se não houver)
