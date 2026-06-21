# Delta for Lancamentos

## ADDED Requirements

### Requirement: Restricao de tipos especiais no cadastro manual
No cadastro manual de lancamentos, o sistema SHALL impedir selecao dos tipos
`Conciliacao` e `Parcela de Cartao`, pois esses tipos sao gerados por fluxos
especificos do sistema.

#### Scenario: Usuario tenta criar Conciliacao manualmente
- **WHEN** o usuario abre o formulario de novo lancamento manual
- **THEN** o sistema SHALL nao disponibilizar o tipo Conciliacao para selecao

#### Scenario: Usuario tenta criar Parcela de Cartao manualmente
- **WHEN** o usuario abre o formulario de novo lancamento manual
- **THEN** o sistema SHALL nao disponibilizar o tipo Parcela de Cartao para selecao
- **AND** SHALL orientar uso do fluxo de compra parcelada para gerar parcelas

### Requirement: Consistencia entre filtro de status e calculo de saldo
Quando o usuario aplicar filtros de status na tela mensal, o sistema SHALL usar os
mesmos criterios de status para listagem de lancamentos e para calculo de saldo
exibido, sem divergencia entre os dois resultados.

#### Scenario: Filtro por status gera lista e saldo coerentes
- **WHEN** o usuario seleciona apenas status Pago e Previsto
- **THEN** o sistema SHALL exibir somente lancamentos desses status
- **AND** SHALL calcular o saldo exibido com base no mesmo subconjunto de lancamentos
