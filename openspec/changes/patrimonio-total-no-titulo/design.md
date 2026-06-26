## Context

A tela de Visao de patrimonio ja calcula e exibe saldo acumulado por conta de
investimento, mas nao mostra um total consolidado no cabecalho. O usuario quer
um resumo imediato no proprio titulo, com a mesma formatacao monetaria usada no
sistema e com total zerado quando nao houver contas.

## Goals / Non-Goals

**Goals:**
- Expor no contexto da view um `total_patrimonio` com a soma dos saldos das
  contas de investimento.
- Exibir no template o titulo no formato `Visao de patrimonio: Total <valor>`.
- Reutilizar o filtro `moeda` para formatacao consistente no cabecalho.
- Cobrir com testes o caso com contas e o caso sem contas.

**Non-Goals:**
- Alterar regras de calculo de `saldo_investimento`.
- Incluir contas Banco ou Cartao no total da Visao de patrimonio.
- Mudar estrutura de tabela/cards de movimentos.

## Decisions

1. Calcular `total_patrimonio` na view somando os mesmos valores ja usados para
   preencher `dados[*].saldo`.
   - Rationale: evita divergencia entre cards e cabecalho.

2. Passar `total_patrimonio` explicitamente para o template.
   - Rationale: mantem template simples e evita logica de agregacao em HTML.

3. Renderizar o titulo com filtro `moeda`, inclusive no caso sem contas.
   - Rationale: garante `R$ 0,00` automaticamente sem tratamento especial de UI.

## Risks / Trade-offs

- [Risco] Duplicar calculo de saldo por conta ao montar `dados` e total -> Mitigacao: calcular saldo uma vez por conta e reutilizar para item e soma.
- [Trade-off] A tela passa a depender de mais uma chave de contexto (`total_patrimonio`) -> Mitigacao: cobrir com testes de renderizacao para detectar regressao cedo.
