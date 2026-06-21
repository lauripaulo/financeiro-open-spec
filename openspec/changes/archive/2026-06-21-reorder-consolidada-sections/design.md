## Context

A view `visualizacao/views.py:visao_consolidada` ja monta todo o contexto necessario (totais, lancamentos, pendentes, contas para ajuste) em uma unica passada, independente da ordem em que os blocos sao renderizados no template. A mudanca e puramente de apresentacao.

## Goals / Non-Goals

**Goals:**
- Colocar Movimentacoes logo depois de Filtros, dando mais destaque a informacao mais usada.
- Mover acoes administrativas/pouco frequentes (Ajustar saldo inicial) para o fim da pagina.

**Non-Goals:**
- Alterar calculo de totais/saldo, filtros ou qualquer regra de negocio.
- Alterar a view `visao_consolidada` ou o contrato de contexto passado ao template.

## Decisions

1. **Reordenar apenas os blocos `<section class="card">` no template**
   - **Decisao:** mover os blocos inteiros (`Movimentacoes`, `Totais`, `Pendentes do mes anterior`, `Ajustar saldo inicial`) em `templates/visualizacao/consolidada.html`, sem tocar em `views.py`.
   - **Racional:** cada secao e auto-contida (usa apenas variaveis de contexto independentes umas das outras), entao reordenar no template e suficiente e nao tem efeito colateral.
   - **Alternativas consideradas:**
     - Tornar a ordem configuravel via preferencia do usuario: rejeitada por excesso de complexidade para um ajuste de UX simples.

## Risks / Trade-offs

- **[Trade-off]** Nenhum risco funcional identificado - mudanca e apenas de posicionamento visual (DOM), formularios HTMX existentes mantem seus `hx-target`/`hx-post` inalterados.

## Migration Plan

1. Reordenar os blocos no template `consolidada.html`.
2. Validar manualmente a nova ordem e rodar a suite de testes existente.
3. Deploy sem migracao de dados; rollback por revert de codigo caso necessario.

## Open Questions

- *(none)*
