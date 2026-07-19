# Design: paginar-movimentacoes-consolidada

## Context

A Visao consolidada (`visualizacao/views.py::visao_consolidada`) obtem os
dados de `resumo_consolidado()` (`visualizacao/services.py`), que materializa
a lista completa de lancamentos do mes — necessaria para calcular
`total_entradas`, `total_saidas` e `saldo_total` — e a devolve no dataclass
`ResumoMes`. O template `templates/visualizacao/consolidada.html` itera essa
lista inteira na tabela de Movimentacoes. Filtros (`ano`, `mes`, `conta`,
`status`) viajam na querystring; a navegacao e por links GET completos, e as
acoes POST (pagar, excluir, transferir) usam HTMX com `HX-Refresh: true`,
que recarrega a URL atual.

## Goals / Non-Goals

**Goals:**
- Paginar a tabela de Movimentacoes em paginas fixas de 50 itens.
- Manter os totais do mes inteiro (sob filtros), independentes da pagina.
- Preservar filtros ativos nos links de paginacao.
- Tolerar valores invalidos de `pagina` sem erro.

**Non-Goals:**
- Paginar Patrimonio, Comparativo ou Pendentes do mes anterior.
- Seletor de tamanho de pagina.
- Paginacao via HTMX/swap parcial — navegacao segue por GET completo.
- Qualquer mudanca em `resumo_consolidado` ou na camada de servico.

## Decisions

1. **Paginacao na view, nao no service.** `resumo_consolidado` ja precisa da
   lista completa para os totais e para o filtro de conta (feito em Python),
   entao paginar no banco nao economizaria consultas. A view aplica
   `django.core.paginator.Paginator(resumo.lancamentos, 50)` e entrega
   `page_obj` ao template. Alternativa rejeitada: service receber `page` —
   vazaria preocupacao de apresentacao para a camada de dominio, contra o
   padrao do repo (services = regra de negocio).

2. **Parametro `pagina` em portugues.** Consistente com `ano`, `mes`,
   `conta`, `status`. Alternativa rejeitada: `page` (default do Django)
   misturaria ingles na URL.

3. **`Paginator.get_page()` para tolerancia.** Nao numerico cai na pagina 1,
   fora do alcance clampa para a ultima. Coerente com `_filtros_mes`, que ja
   degrada entrada invalida para defaults silenciosos. Alternativa
   rejeitada: 404/400 — punitivo para app pessoal e destoa do restante.

4. **Reset natural para a pagina 1.** O form de filtros e os links de
   navegacao de mes simplesmente nao carregam `pagina`; ausencia do
   parametro ja significa pagina 1. Nenhum codigo de reset explicito.

5. **Controle minimo abaixo da tabela.** "Anterior / Pagina X de Y /
   Proxima" com estilo `m3-button--text` (mesmo padrao da navegacao de mes),
   renderizado somente quando `page_obj.paginator.num_pages > 1`. Links
   reconstroem a querystring completa com os filtros ativos. Alternativa
   rejeitada: links numerados — volume tipico (1-6 paginas) nao justifica.

6. **Totais intocados.** Cards de Entradas/Saidas/Saldo continuam lendo os
   agregados de `ResumoMes`, calculados sobre a lista completa. Paginacao
   afeta apenas a iteracao da tabela.

## Risks / Trade-offs

- [Acao POST na ultima pagina remove o ultimo item; `HX-Refresh` recarrega
  `?pagina=N` agora fora do alcance] → `get_page()` clampa para a nova
  ultima pagina; sem erro, sem tela vazia.
- [Lista completa segue materializada em memoria] → aceitavel: centenas de
  itens por mes, e os totais exigem a lista inteira de qualquer forma.
- [Links de paginacao construidos a mao no template podem perder um filtro
  futuro] → teste de preservacao de filtros cobre a regressao; construcao
  centralizada em um unico bloco do template.

## Open Questions

Nenhuma — decisoes fechadas em sessao de grilling.
