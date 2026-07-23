## ADDED Requirements

### Requirement: Retorno contextual em formulários iniciados na Visão consolidada
Quando um formulário for aberto a partir da Visão consolidada, o sistema SHALL preservar o contexto de origem para retorno por cancelamento ou por sucesso. O contexto SHALL incluir o mês consultado e SHOULD preservar filtros de conta, status e paginação quando presentes.

#### Scenario: Cancelamento retorna ao contexto de origem
- **GIVEN** o usuário está na Visão consolidada com mês, conta e status filtrados
- **WHEN** ele abre um formulário de novo lançamento, edição, compra parcelada ou transferência e aciona `Cancelar`
- **THEN** o sistema SHALL retornar à Visão consolidada com o mesmo mês e filtros de origem

#### Scenario: Salvamento retorna ao contexto de origem
- **GIVEN** o usuário abriu um formulário a partir da Visão consolidada filtrada
- **WHEN** ele salva o formulário com sucesso
- **THEN** o sistema SHALL retornar à Visão consolidada preservando o contexto de origem quando seguro

#### Scenario: URL de retorno externa é ignorada
- **GIVEN** um formulário recebe uma URL de retorno externa ao sistema
- **WHEN** o usuário cancela ou salva com sucesso
- **THEN** o sistema SHALL ignorar a URL externa
- **AND** SHALL usar o fallback local definido para o fluxo

### Requirement: Seleção de mês nas visões mensais
As telas de consulta mensal SHALL permitir escolher competência mês/ano por um controle mensal único, preservando a navegação existente por mês anterior e mês seguinte.

#### Scenario: Visão consolidada mantém navegação rápida
- **WHEN** o usuário acessa a Visão consolidada
- **THEN** a tela SHALL continuar exibindo ações de mês anterior e mês seguinte
- **AND** SHALL oferecer um controle único para escolher outra competência mês/ano

#### Scenario: Comparativo usa duas competências mensais
- **WHEN** o usuário acessa o Comparativo
- **THEN** a tela SHALL permitir selecionar a competência A e a competência B por controles mensais
- **AND** SHALL comparar os saldos dos meses selecionados
