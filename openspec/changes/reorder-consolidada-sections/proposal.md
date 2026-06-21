## Why

Na tela de Visao consolidada, a tabela de Movimentacoes (a informacao mais consultada no dia a dia) aparece apenas no final da pagina, depois de blocos de uso ocasional como "Ajustar saldo inicial" e "Pendentes do mes anterior". Isso obriga o usuario a rolar a pagina toda para ver os lancamentos do mes logo depois de aplicar um filtro.

## What Changes

- Reordenar as secoes da tela de Visao consolidada para que Movimentacoes apareca imediatamente apos Filtros, seguida de Totais, Pendentes do mes anterior e, por ultimo, Ajustar saldo inicial.
- Nenhuma logica de calculo, rota ou dado exibido muda - apenas a ordem de apresentacao dos blocos na pagina.

## Capabilities

### New Capabilities
- *(none)*

### Modified Capabilities
- `visualizacao`: formalizar a ordem de apresentacao das sessões na tela principal.

## Impact

- Templates HTMX: `templates/visualizacao/consolidada.html`.
- Nenhum impacto em `visualizacao/views.py`, models ou outras apps.
