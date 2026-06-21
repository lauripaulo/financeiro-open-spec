# Delta for Visualizacao

## ADDED Requirements

### Requirement: Ordem das secoes na tela principal
Na tela principal (Visao consolidada), o sistema SHALL apresentar as secoes de
conteudo na seguinte ordem: Cabecalho (navegacao de mes), Avisos, Filtros,
Movimentacoes, Totais, Pendentes do mes anterior e, por ultimo, Ajustar saldo
inicial.

#### Scenario: Usuario acessa a tela principal com um mes ja criado
- **WHEN** o usuario acessa a Visao consolidada de um mes ja criado
- **THEN** o sistema SHALL exibir a secao de Movimentacoes imediatamente apos os
  Filtros
- **AND** SHALL exibir Totais, Pendentes do mes anterior e Ajustar saldo inicial,
  nessa ordem, apos Movimentacoes
