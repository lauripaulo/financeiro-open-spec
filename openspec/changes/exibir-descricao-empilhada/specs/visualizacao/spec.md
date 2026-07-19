# Delta: visualizacao — exibir-descricao-empilhada

## ADDED Requirements

### Requirement: Exibicao empilhada da descricao nas listagens
O sistema SHALL exibir empilhada, nas Movimentacoes da Visao consolidada e
no preview da importacao, toda descricao contendo " - ": o trecho anterior
ao primeiro " - " na linha principal e o restante em linha secundaria com
enfase visual reduzida. A coluna Descricao SHALL ter largura maxima com
quebra de linha, de modo que descricoes longas SHALL NOT causar
transbordamento horizontal da tabela. Nas Movimentacoes, quando o
lancamento possuir Detalhes, a celula da descricao SHALL expor o texto
completo dos Detalhes via dica flutuante (atributo `title`). O dado da
descricao SHALL NOT ser alterado — o empilhamento e exclusivamente de
apresentacao.

#### Scenario: Descricao importada exibe operacao e contraparte empilhadas
- **GIVEN** um lancamento com descricao "Transferencia enviada pelo Pix - JOAO DA SILVA"
- **WHEN** o usuario visualiza as Movimentacoes
- **THEN** a linha principal SHALL exibir "Transferencia enviada pelo Pix"
- **AND** a linha secundaria SHALL exibir "JOAO DA SILVA" com enfase reduzida

#### Scenario: Descricao sem separador permanece em linha unica
- **GIVEN** um lancamento com descricao "Aluguel"
- **WHEN** o usuario visualiza as Movimentacoes
- **THEN** a descricao SHALL ser exibida sem linha secundaria

#### Scenario: Somente o primeiro separador divide a descricao
- **GIVEN** um lancamento com descricao "Pix - Loja - Filial Centro"
- **WHEN** o usuario visualiza as Movimentacoes
- **THEN** a linha principal SHALL exibir "Pix"
- **AND** a linha secundaria SHALL exibir "Loja - Filial Centro"

#### Scenario: Lancamento com detalhes expoe memo completo por dica
- **GIVEN** um lancamento importado cuja descricao foi encurtada e cujos
  Detalhes guardam o memo integral
- **WHEN** o usuario visualiza as Movimentacoes
- **THEN** a celula da descricao SHALL conter o memo integral no atributo
  `title`

#### Scenario: Preview da importacao usa o mesmo empilhamento
- **GIVEN** um item de preview de importacao com descricao contendo " - "
- **WHEN** o usuario visualiza o preview
- **THEN** a descricao SHALL ser exibida empilhada como nas Movimentacoes
