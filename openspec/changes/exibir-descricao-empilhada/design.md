# Design: exibir-descricao-empilhada

## Context

`resumir_memo()` (`importacao/services.py`) ja reduz o memo do OFX a
"operacao - contraparte" (cap 180 chars) e guarda o memo integral em
`detalhes`. Ainda assim a descricao estoura a tabela de Movimentacoes:
`.m3-data-table th, td { white-space: nowrap; }` em
`static/css/m3-components.css` impede qualquer quebra — a celula cresce com
o texto e o wrapper vira scroll horizontal.

## Goals / Non-Goals

**Goals:**
- Descricao nunca estoura o layout da tabela.
- Hierarquia visual: operacao em destaque, contraparte secundaria.
- Memo completo acessivel por hover nas Movimentacoes.

**Non-Goals:**
- Alterar o dado `descricao` (nada de `<br/>` ou encurtamento adicional).
- Tocar `resumir_memo` ou qualquer service.
- Patrimonio, pendentes e demais listagens (so Movimentacoes + preview de
  importacao).

## Decisions

1. **Correcao na apresentacao, dado intacto.** `<br/>` gravado na descricao
   quebraria form de edicao, busca e exports, e exigiria `|safe` sobre dado
   de arquivo externo (XSS). Rejeitado.
2. **Split estruturado no primeiro " - "** via template filter
   `partes_descricao` em `visualizacao/templatetags/descricao.py` (padrao de
   `moeda.py`): linha principal + `<span class="m3-descricao-secundaria">`
   em bloco, menor e apagada. Django nao tem filter `split` nativo.
3. **Split para qualquer descricao com " - "**, nao so importadas —
   consistencia na mesma tabela; parcelas ("Loja - Parcela 2/10") ate
   melhoram. Alternativa rejeitada: condicionar a `detalhes` preenchido
   (acopla apresentacao a origem do dado).
4. **Teto CSS como garantia**: `.m3-cell-descricao { white-space: normal;
   max-width: 32ch; overflow-wrap: anywhere; }` — cobre contraparte gigante
   sem " - ". Tipografia da linha secundaria usa tokens `label-medium`
   (`body-small` nao existe em `m3-tokens.css`).
5. **Tooltip `title` com `detalhes`** quando presente — custo zero, sem JS.
   So nas Movimentacoes; itens do preview sao dicts de `_item_resumo` sem
   `detalhes`.

## Risks / Trade-offs

- [Descricao manual com " - " intencional ganha empilhamento] → aceito por
  decisao explicita; visual continua legivel.
- [`title` nao funciona em touch] → memo completo segue acessivel na tela de
  edicao; tooltip e conveniencia, nao unico caminho.
- [Filter novo em `visualizacao` usado por template de `importacao`] →
  aceitavel: templatetags sao registrados globalmente pelo Django; se surgir
  terceiro consumidor, promover para app compartilhado.

## Open Questions

Nenhuma — decisoes fechadas em grilling e plano aprovado.
