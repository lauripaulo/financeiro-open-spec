# Tasks: exibir-descricao-empilhada

## 1. Template filter

- [x] 1.1 Criar `visualizacao/templatetags/descricao.py` com filter
      `partes_descricao` (split no primeiro " - ", partes com strip),
      seguindo o padrao de `moeda.py`.

## 2. Templates

- [x] 2.1 `templates/visualizacao/consolidada.html`: carregar `descricao`,
      celula da descricao com classe `m3-cell-descricao`, linha principal +
      span `m3-descricao-secundaria`, e `title` com `detalhes` quando
      presente.
- [x] 2.2 `templates/importacao/_tabela_itens.html`: mesmo empilhamento na
      celula da descricao (sem `title`).

## 3. CSS

- [x] 3.1 `static/css/m3-components.css`: `.m3-data-table
      td.m3-cell-descricao` (white-space normal, max-width 32ch,
      overflow-wrap anywhere) e `.m3-descricao-secundaria` (display block,
      cor on-surface-variant, tipografia label-medium).

## 4. Testes

- [x] 4.1 Filter: "A - B - C" divide em ["A", "B - C"]; "A" fica ["A"];
      "A - B" divide em ["A", "B"].
- [x] 4.2 Render Movimentacoes: descricao com " - " gera span secundaria com
      o restante; sem " - " nao gera span; lancamento com detalhes gera
      `title` com o memo completo.
- [x] 4.3 Render preview importacao: item com " - " gera span secundaria.

## 5. Verificacao

- [x] 5.1 `.venv/bin/python manage.py test visualizacao importacao` e suite
      completa.
- [x] 5.2 `openspec validate --changes` sem erros.
