## MODIFIED Requirements

### Requirement: Restricao de tipos especiais no cadastro manual
No cadastro manual de lancamentos, o sistema SHALL impedir selecao dos tipos
`Conciliacao` e `Parcela de Cartao`, pois esses tipos sao gerados por fluxos
especificos do sistema. Contudo, ao editar um lancamento existente desses tipos,
o sistema SHALL permitir a edicao de seus outros campos, desabilitando o campo
tipo para garantir que permaneca inalterado.

#### Scenario: Usuario tenta criar Conciliacao manualmente
- **WHEN** o usuario abre o formulario de novo lancamento manual
- **THEN** o sistema SHALL nao disponibilizar o tipo Conciliacao para selecao

#### Scenario: Usuario tenta criar Parcela de Cartao manualmente
- **WHEN** o usuario abre o formulario de novo lancamento manual
- **THEN** o sistema SHALL nao disponibilizar o tipo Parcela de Cartao para selecao
- **AND** SHALL orientar uso do fluxo de compra parcelada para gerar parcelas

#### Scenario: Usuario edita Parcela de Cartao existente
- **WHEN** o usuario abre a edicao de um lancamento existente do tipo Parcela de Cartao
- **THEN** o sistema SHALL disponibilizar o tipo Parcela de Cartao no formulario
- **AND** SHALL desabilitar a alteracao do campo tipo
