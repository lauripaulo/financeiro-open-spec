## ADDED Requirements

### Requirement: Cobertura completa de calendário nativo para datas reais
Todo campo que representa uma data real com dia, mês e ano SHALL usar entrada nativa de data (`type="date"`) para abrir o calendário do navegador. Essa regra SHALL cobrir, no mínimo, vencimento de lançamento, pagamento de lançamento, data da compra parcelada, data de transferência e data de referência do planejamento.

#### Scenario: Planejamento usa calendário nativo
- **WHEN** o usuário acessa a tela de Planejamento Financeiro
- **THEN** o campo Data de referência SHALL ser renderizado como `type="date"`

#### Scenario: Pagamento em popover usa calendário nativo
- **WHEN** o usuário abre a ação de pagar um lançamento na Visão consolidada
- **THEN** o campo de data de pagamento SHALL ser renderizado como `type="date"`

### Requirement: Competência mensal não é data real
Campos que representam apenas uma competência mês/ano SHALL NOT ser tratados como data completa de vencimento ou pagamento. Esses campos SHALL usar controle mensal nativo (`type="month"`) ou componente equivalente, e o sistema SHALL converter a competência selecionada para os parâmetros internos `ano` e `mes`.

#### Scenario: Comparativo seleciona competências mensais
- **WHEN** o usuário acessa o Comparativo entre meses
- **THEN** cada mês comparado SHALL ser selecionado por controle de competência mensal
- **AND** o sistema SHALL interpretar a seleção como mês/ano, sem exigir dia do mês

#### Scenario: Visão consolidada aceita competência mensal
- **WHEN** o usuário altera o mês consultado na Visão consolidada por um controle de competência mensal
- **THEN** o sistema SHALL exibir o mês e ano selecionados
- **AND** SHALL manter compatibilidade com parâmetros internos `ano` e `mes`
