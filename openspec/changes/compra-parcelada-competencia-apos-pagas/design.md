## Context

A mudanca anterior de `parcelas_pagas` preservou a numeracao original da serie
(`N/total`), mas reaproveitou o mesmo indice para calcular o mes da parcela.
Com isso, quando ha parcelas pagas, a primeira parcela restante ficou com
competencia deslocada para frente (ex.: 6/10 indo para dezembro), em vez de
iniciar no mes seguinte da compra como esperado no fluxo de planejamento futuro.

O usuario confirmou a regra desejada: para compras com parcelas pagas, as
parcelas restantes devem manter a numeracao original, mas a competencia e o
vencimento devem recomecar no mes seguinte a `data_compra` sem pular meses.

## Goals / Non-Goals

**Goals:**
- Corrigir o calendario de geracao parcial para iniciar no mes seguinte da compra.
- Manter `parcela_atual` e descricao `N/total` da serie original.
- Aplicar a mesma regra corrigida em `competencia_ano/mes` e `data_vencimento`.
- Garantir cobertura de testes para o caso com parcelas pagas e para o caso base.

**Non-Goals:**
- Alterar validacoes de `parcelas_pagas` ja implementadas.
- Alterar calculo monetario das parcelas.
- Persistir informacoes adicionais em banco.

## Decisions

1. Separar dois indices na geracao:
   - indice de numeracao (`parcela_atual`) baseado na serie original
   - indice de calendario baseado na posicao dentro das parcelas restantes
   Rationale: resolve o bug sem perder rastreabilidade da serie.

2. Calcular mes/ano de vencimento a partir do indice relativo da parcela gerada
   (0, 1, 2...) sempre somando ao mes da compra + 1.
   Rationale: garante continuidade mensal das parcelas restantes.

3. Preservar o calculo de valor por parcela usando `total_parcelas` original.
   Rationale: escopo desta correcao e apenas temporal/competencia.

## Risks / Trade-offs

- [Risco] Regressao no caso sem parcelas pagas por ajuste de loop/indexacao -> Mitigacao: manter teste existente do fluxo 10x sem pagas.
- [Risco] Divergencia entre `parcela_atual` e mes de competencia pode parecer incomum para compras antigas -> Mitigacao: comportamento e intencional e alinhado ao uso confirmado no grilling.
- [Trade-off] Maior complexidade no loop com dois indices -> Mitigacao: nomes explicitos e testes de exemplo concreto (10x com 5 pagas).
