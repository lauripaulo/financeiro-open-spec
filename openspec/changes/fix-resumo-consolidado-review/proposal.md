# Proposal: fix-resumo-consolidado-review

## Why

O review de duas eixos (standards + spec) do commit `1eb0026` (change `add-resumo-consolidado-service`) apontou 6 achados. O mais grave: `resumo_consolidado` re-implementa inline a regra de saldo mensal (fallback de `saldo_inicial` + entradas − saidas) que a propria change acabou de unificar em `saldo_do_mes` — a "implementacao unica" prometida pela spec virou duas copias acopladas so por docstring e teste de concordancia. Alem disso: parse de `conta_id` (input HTTP) acontece dentro do service, o cenario "cada saldo concorda com `saldo_do_mes`" so e testado transitivamente (cartao nunca verificado individualmente), o campo `conta_selecionada` do `ResumoMes` ficou fora do contrato especificado, e a docstring subestima o numero de consultas.

## What Changes

- Criar `saldos_do_mes(contas, ano, mes, status_incluidos=None)` em `meses/services.py`: versao batch da regra de saldo, uma consulta de lancamentos para todas as contas, retorna dict `{conta_id: saldo}`. `saldo_do_mes` vira wrapper fino sobre ela — a regra passa a ter exatamente uma implementacao, morando no app dono (`meses`).
- `resumo_consolidado` deleta sua copia inline da regra e chama `saldos_do_mes`. Orcamento de consultas passa de 3 para 4 (contas, lancamentos exibidos, lancamentos para saldo, `SaldoMensalConta`) — constante, sem N+1; trade aceito em favor de dono unico da regra.
- Parse de `conta_id` sai do service: a view converte para `int` (unica camada que interpreta request); `resumo_consolidado` passa a aceitar `conta_id: int | None`.
- Teste de concordancia vira por conta: itera todas as contas e afirma o saldo individual de cada uma contra `saldo_do_mes`, com e sem filtro de status — cartao deixa de ser verificado so por transitividade.
- Campo `conta_selecionada` do `ResumoMes` legitimado no contrato da capability (7 campos), com a regra: interpretacao de parametros de request permanece na view; o service apenas resolve a `Conta` ja validada como inteiro.
- Docstring de `resumo_consolidado` corrigida para o numero real de consultas.
- Comportamento visivel ao usuario permanece identico.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `resumo-consolidado`: (1) requisito "Regra de saldo mensal com implementacao unica" passa a exigir que a implementacao unica seja `saldos_do_mes` (batch) em `meses/services.py`, consumida por `saldo_do_mes` e por `resumo_consolidado` — copia inline em qualquer outro modulo deixa de ser permitida; (2) requisito "Service unico de consolidacao mensal" passa a documentar o campo `conta_selecionada` e a assinatura `conta_id: int | None`; (3) requisito "Consolidacao em passada unica" ajustado: numero constante de consultas (4), sem recomputo por conta, em vez de "3 consultas".

Nota de sequenciamento: a capability `resumo-consolidado` ainda vive como delta na change `add-resumo-consolidado-service` (nao arquivada). Arquivar aquela change antes desta, para que o MODIFIED aqui aplique sobre a spec principal ja sincronizada.

## Impact

- **Codigo**: `meses/services.py` (nova `saldos_do_mes`, `saldo_do_mes` vira wrapper), `visualizacao/services.py` (remove regra inline e parse de string, docstring), `visualizacao/views.py` (parse de `conta_id` para int).
- **Testes**: concordancia por conta (todas as contas, com/sem status), `assertNumQueries` 3→4, teste direto de `saldos_do_mes` em `meses/tests.py`.
- **Performance**: +1 consulta constante na tela principal; segue O(1) em numero de contas, sem N+1.
- **Risco**: baixo — refactor interno com suite de 118 testes como rede; comportamento HTTP identico (inclusive `ValueError` em `?conta=abc`, que continua nascendo do parse, agora na view).
