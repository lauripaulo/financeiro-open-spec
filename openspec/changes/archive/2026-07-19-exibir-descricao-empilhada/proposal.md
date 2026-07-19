# Proposal: exibir-descricao-empilhada

## Why

Descricoes importadas de OFX ("operacao - contraparte") estouram o layout da
tabela de Movimentacoes: o CSS da tabela proibe quebra de linha
(`white-space: nowrap`), entao a celula cresce com o texto e forca scroll
horizontal. A alternativa de gravar `<br/>` na descricao foi rejeitada —
apresentacao nao pertence ao dado (quebraria form de edicao, busca e exports,
e abriria XSS).

## What Changes

- Descricao com " - " passa a ser exibida empilhada: operacao na linha
  principal, restante em linha secundaria menor e apagada. Vale para
  qualquer lancamento (importado, manual, parcela).
- Coluna Descricao ganha teto de largura com quebra normal — nunca mais
  estoura, mesmo contraparte gigante.
- Celula da descricao nas Movimentacoes exibe o memo completo (`detalhes`)
  via tooltip (`title`) quando presente.
- Mesmo tratamento visual no preview da importacao (sem tooltip — itens de
  preview nao carregam `detalhes`).
- Dado `descricao` permanece intacto; mudanca 100% de apresentacao.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `visualizacao`: novo requisito de exibicao da descricao em linha principal
  + secundaria, teto de largura da coluna e acesso ao memo completo via
  tooltip.

## Impact

- `visualizacao/templatetags/descricao.py` — novo filter `partes_descricao`.
- `templates/visualizacao/consolidada.html` — celula da descricao empilhada
  + tooltip.
- `templates/importacao/_tabela_itens.html` — celula da descricao empilhada.
- `static/css/m3-components.css` — regras `.m3-cell-descricao` e
  `.m3-descricao-secundaria`.
- `visualizacao/tests.py` (e render do preview) — testes de filter e
  renderizacao.
- Sem migracao, sem mudanca de modelo ou de servicos.
