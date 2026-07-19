# Proposal: paginar-movimentacoes-consolidada

## Why

Com a importacao de OFX (fatura de cartao e extrato de conta), um mes pode
concentrar centenas de lancamentos. A tabela de Movimentacoes da Visao
consolidada renderiza tudo de uma vez, tornando a pagina longa e lenta de
percorrer.

## What Changes

- A tabela de Movimentacoes da Visao consolidada passa a ser paginada em
  paginas fixas de 50 lancamentos.
- Os totais (Entradas, Saidas, Saldo) continuam refletindo o mes inteiro
  (respeitando filtros de conta e status) — nunca apenas a pagina visivel.
- Novo parametro de querystring `pagina`; os links de paginacao preservam os
  filtros ativos (`ano`, `mes`, `conta`, `status`).
- Mudar filtros ou navegar entre meses retorna naturalmente a pagina 1.
- Valores invalidos de `pagina` sao tolerados: nao numerico cai na pagina 1,
  fora do alcance cai na ultima pagina.
- Controle de paginacao "Anterior / Pagina X de Y / Proxima" abaixo da
  tabela, oculto quando ha apenas uma pagina.
- Escopo restrito a Movimentacoes: Patrimonio, Comparativo e Pendentes do
  mes anterior nao paginam.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `visualizacao`: novo requisito de paginacao das Movimentacoes na Visao
  consolidada (tamanho de pagina, preservacao de filtros, tolerancia a
  pagina invalida, visibilidade do controle) e garantia explicita de que os
  totais permanecem do mes inteiro sob paginacao.

## Impact

- `visualizacao/views.py` — `visao_consolidada` pagina `resumo.lancamentos`
  com `django.core.paginator.Paginator`; `resumo_consolidado` em
  `visualizacao/services.py` permanece intocado (totais precisam da lista
  completa).
- `templates/visualizacao/consolidada.html` — itera a pagina e ganha o
  controle de paginacao.
- `visualizacao/tests.py` — novos testes de divisao de paginas, totais sob
  paginacao, clamp de pagina invalida, preservacao de filtros e ocultacao
  do controle.
- Sem migracao, sem mudanca de modelo, sem nova dependencia.
