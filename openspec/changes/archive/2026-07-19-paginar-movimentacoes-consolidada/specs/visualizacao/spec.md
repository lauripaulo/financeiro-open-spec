# Delta: visualizacao — paginar-movimentacoes-consolidada

## ADDED Requirements

### Requirement: Paginacao das Movimentacoes na Visao consolidada
O sistema SHALL paginar a tabela de Movimentacoes da Visao consolidada em
paginas de 50 lancamentos, controladas pelo parametro de querystring
`pagina`. Os links de paginacao SHALL preservar os filtros ativos (`ano`,
`mes`, `conta`, `status`). O controle de paginacao SHALL exibir
"Anterior / Pagina X de Y / Proxima" abaixo da tabela e SHALL NOT ser
exibido quando houver apenas uma pagina. Valores invalidos de `pagina`
SHALL ser tolerados sem erro: valor nao numerico resulta na pagina 1 e
valor fora do alcance resulta na ultima pagina.

#### Scenario: Mes com mais de 50 lancamentos e dividido em paginas
- **GIVEN** um mes com 51 lancamentos em contas Banco/Cartao
- **WHEN** o usuario acessa a Visao consolidada sem parametro `pagina`
- **THEN** a tabela de Movimentacoes SHALL exibir os primeiros 50
  lancamentos da ordenacao por data de vencimento
- **AND** a pagina 2 SHALL exibir o lancamento restante

#### Scenario: Links de paginacao preservam filtros ativos
- **GIVEN** a Visao consolidada filtrada por conta e status
- **WHEN** o usuario navega para outra pagina pelo controle de paginacao
- **THEN** os links de paginacao SHALL conter `ano`, `mes`, `conta` e
  `status` da consulta atual

#### Scenario: Pagina invalida degrada sem erro
- **WHEN** o usuario acessa a Visao consolidada com `pagina` nao numerico
- **THEN** o sistema SHALL exibir a pagina 1
- **WHEN** o usuario acessa com `pagina` maior que o total de paginas
- **THEN** o sistema SHALL exibir a ultima pagina

#### Scenario: Controle oculto com uma unica pagina
- **GIVEN** um mes com 50 lancamentos ou menos
- **WHEN** o usuario acessa a Visao consolidada
- **THEN** o controle de paginacao SHALL NOT ser exibido

#### Scenario: Mudanca de filtro ou de mes retorna a pagina 1
- **GIVEN** o usuario esta na pagina 2 das Movimentacoes
- **WHEN** o usuario aplica um filtro ou navega para outro mes
- **THEN** o sistema SHALL exibir a pagina 1 do novo recorte

### Requirement: Totais do mes independentes da paginacao
Os totais de Entradas, Saidas e Saldo da Visao consolidada SHALL refletir
todos os lancamentos do mes que atendem aos filtros ativos,
independentemente da pagina de Movimentacoes exibida.

#### Scenario: Totais iguais em todas as paginas
- **GIVEN** um mes com 51 lancamentos distribuidos em duas paginas
- **WHEN** o usuario compara os cards de totais da pagina 1 e da pagina 2
- **THEN** os valores de Entradas, Saidas e Saldo SHALL ser identicos e
  corresponder ao mes inteiro
