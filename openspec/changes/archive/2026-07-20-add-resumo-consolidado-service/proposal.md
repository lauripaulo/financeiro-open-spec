# Proposal: add-resumo-consolidado-service

## Why

A visao consolidada e o coracao do app, mas toda a sua logica de consolidacao (filtros, totais de entradas/saidas, saldo por conta, saldo inicial com fallback, alertas de limite) vive inline em `visualizacao/views.py:57-156` — sem interface propria, testavel apenas via HTTP. Alem disso, a regra de saldo mensal (`saldo_inicial` com fallback em `conta.saldo_atual` + soma de entradas − saidas) esta duplicada em 3 lugares: `_saldo_final_periodo` (meses/services.py:31), `saldo_do_mes` (meses/services.py:244) e loops inline na view consolidada. Uma mudanca na semantica de `SaldoMensalConta` exige editar multiplos pontos que podem divergir. A arquitetura declarada (CLAUDE.md e arquitetura.md) exige logica de negocio em `services.py` por app — `visualizacao` e o unico app sem `services.py`.

## What Changes

- Criar `visualizacao/services.py` com `resumo_consolidado(ano, mes, conta_id=None, status=None)` retornando um value object `ResumoMes` com: lista de lancamentos filtrados, totais de entradas/saidas, saldo total, saldos iniciais por conta (`contas_ajuste`) e alertas de limite negativo — em passada unica, eliminando o recomputo duplo de `saldo_do_mes` e o N+1 de `SaldoMensalConta`.
- Reduzir `visao_consolidada` a dispatch + render (~20 linhas): parse de filtros, gate de mes aberto, chamada ao service, contexto de template.
- Deletar `_saldo_final_periodo` de `meses/services.py` — e identico a `saldo_do_mes` com `status_incluidos=None`. Rotear `criar_mes` (linha 121) por `saldo_do_mes`.
- Fazer `resumo_consolidado` usar `saldo_do_mes` (ou logica equivalente em passada unica) como unica implementacao da regra de saldo — nenhuma copia inline da regra sobrevive na view.
- Comportamento visivel ao usuario permanece identico: mesmos totais, mesmos alertas, mesma renderizacao.

## Capabilities

### New Capabilities

- `resumo-consolidado`: contrato do service de consolidacao mensal — uma unica interface computa lancamentos filtrados, totais, saldos por conta e alertas de limite para um mes, sem depender de HTTP; regra de saldo mensal tem implementacao unica no sistema.

### Modified Capabilities

Nenhuma. Requisitos de `visualizacao` e `meses` nao mudam — totais, alertas, filtros e encadeamento de saldo continuam com o mesmo comportamento observavel. A mudanca e estrutural (onde a logica vive), nao comportamental.

## Impact

- **Codigo**: `visualizacao/services.py` (novo), `visualizacao/views.py` (view `visao_consolidada` encolhe de ~100 para ~20 linhas), `meses/services.py` (remocao de `_saldo_final_periodo`, `criar_mes` passa a usar `saldo_do_mes`).
- **Testes**: novos testes de `resumo_consolidado` direto no service (sem client HTTP); testes existentes da view consolidada continuam passando como rede de seguranca de regressao.
- **Performance**: elimina recomputo duplo de saldo por conta e consultas N+1 de `SaldoMensalConta` na tela principal.
- **Risco**: baixo — mudanca puramente aditiva ate a troca final da view; sem migracao de dados, sem mudanca de template.
