## Por que

A implementacao atual permite dois escritores para `PARCELA_CARTAO` (fluxo de compra parcelada e abertura de mes), o que pode gerar parcelas duplicadas e ambiguidade sobre a responsabilidade pelo ciclo de vida das parcelas. A criacao de mes tambem permite abrir meses arbitrarios, o que quebra a cadeia temporal esperada e introduz inconsistencias em propagacao e saldos.

## O que muda

- Tornar `CompraParcelada` a fonte unica de verdade para geracao de parcelas `PARCELA_CARTAO`.
- Remover a geracao de `PARCELA_CARTAO` da propagacao de abertura de mes.
- Enforcar regras de sequencia para abertura de mes:
  - o primeiro mes aberto deve ser o mes atual;
  - apos o primeiro, somente o mes imediatamente seguinte pode ser aberto (sem pular).
- Manter comportamento idempotente quando for solicitado um mes que ja esta aberto.
- Remover `PARCELA_CARTAO` da semantica de cascata de recorrencia usada nos fluxos de editar/excluir recorrentes.
- Melhorar o feedback ao usuario em tentativas invalidas de abertura de mes, mostrando o mes permitido.
- Atualizar documentacao e testes para refletir o comportamento canonico, incluindo atualizacao do README ao final da execucao.

## Capacidades

### Novas capacidades
- *(nenhuma)*

### Capacidades modificadas
- `meses`: abertura de mes passa a ser estritamente sequencial e deixa de propagar `PARCELA_CARTAO`.
- `parcelas`: a geracao de parcelas passa a ser explicitamente de responsabilidade apenas do fluxo de compra.
- `lancamentos`: `PARCELA_CARTAO` deixa de participar de comportamento de cascata em serie recorrente.
- `visualizacao`: feedback da UI de abertura de mes passa a comunicar o mes permitido quando a regra de sequencia for violada.

## Impacto

- Services de backend em `meses/services.py` e comportamento de compra/parcelas em `parcelas/services.py`.
- Classificacao de recorrencia em `lancamentos/models.py` e fluxos relacionados de edicao/exclusao.
- Fluxo de feedback de abertura de mes em `visualizacao/views.py` e templates.
- Deltas de spec OpenSpec para `meses`, `parcelas`, `lancamentos` e `visualizacao`.
- Atualizacoes da suite de testes para restricoes de sequencia de meses e nao duplicacao de parcelas.
