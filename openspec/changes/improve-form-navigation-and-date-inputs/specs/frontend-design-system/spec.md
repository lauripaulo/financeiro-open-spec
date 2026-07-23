## ADDED Requirements

### Requirement: Ações secundárias em formulários de usuário
Todo formulário renderizado nas páginas de usuário SHALL exibir uma ação secundária ao lado da ação primária. Formulários de criação ou edição com risco de perda de dados SHALL usar o rótulo `Cancelar`; fluxos sem edição persistente em andamento SHALL usar o rótulo `Voltar`. A ação secundária SHALL navegar sem submeter o formulário.

#### Scenario: Formulário CRUD exibe Cancelar
- **WHEN** o usuário acessa um formulário de criação ou edição de conta, lançamento, compra parcelada ou transferência
- **THEN** o formulário SHALL exibir a ação primária do fluxo
- **AND** SHALL exibir uma ação secundária `Cancelar` que navega sem submeter o formulário

#### Scenario: Fluxo operacional exibe Voltar
- **WHEN** o usuário acessa um formulário operacional sem edição persistente em andamento, como importação OFX antes do envio
- **THEN** o formulário SHALL exibir uma ação secundária `Voltar` que navega sem submeter o formulário

#### Scenario: Ações mantêm padrão visual M3
- **WHEN** um formulário exibe ações primária e secundária
- **THEN** a ação primária SHALL usar estilo de botão preenchido M3
- **AND** a ação secundária SHALL usar estilo secundário M3 consistente com demais links/botões da aplicação

### Requirement: Controle visual de competência mensal
Telas que pedem ao usuário uma competência mês/ano SHALL apresentar essa escolha como um controle único de competência mensal, em vez de dois campos numéricos soltos, quando o navegador oferecer suporte nativo adequado.

#### Scenario: Competência mensal aparece como controle único
- **WHEN** o usuário acessa uma tela de consulta que permite escolher mês e ano
- **THEN** a UI SHALL apresentar a competência mês/ano como um controle único ou componente visual equivalente
- **AND** SHALL evitar que o usuário tenha de coordenar manualmente dois campos numéricos independentes
