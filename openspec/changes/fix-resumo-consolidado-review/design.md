# Design: fix-resumo-consolidado-review

## Context

A change `add-resumo-consolidado-service` entregou o service e unificou a regra de saldo deletando `_saldo_final_periodo` — mas, para manter a passada unica em 3 consultas, `resumo_consolidado` re-encodou a regra (fallback + entradas − saidas) em vez de chamar `saldo_do_mes`. O design daquela change registrou a alternativa "dar a `saldo_do_mes` um modo batch" como adiada. O review confirmou que a duplicacao e o custo errado: a regra que os docs do repo tratam como centralizada em `meses` agora tem uma segunda copia em `visualizacao`, protegida so por teste de concordancia. Este fix adota a alternativa adiada.

Achados restantes: parse de `conta_id` string dentro do service (concern HTTP na camada errada), concordancia por conta testada so transitivamente, campo `conta_selecionada` fora do contrato, docstring com contagem de consultas errada.

## Goals / Non-Goals

**Goals:**

- Regra de saldo mensal com um unico corpo de implementacao, no app `meses`: `saldos_do_mes` (batch).
- `resumo_consolidado` sem copia da regra e sem parse de input HTTP.
- Cenario de concordancia coberto por conta (todas), com e sem filtro de status.
- Contrato do `ResumoMes` (7 campos, `conta_id: int | None`) documentado na spec.

**Non-Goals:**

- Mudar comportamento observavel, template ou contexto renderizado.
- Otimizar alem do orcamento constante de consultas (4 e aceitavel; voltar a 3 exigiria vazar a lista de lancamentos entre camadas).
- Tocar os demais candidatos da revisao de arquitetura (pair module, recorrencia etc.).

## Decisions

### 1. `saldos_do_mes(contas, ano, mes, status_incluidos=None)` como implementacao canonica

Assinatura batch em `meses/services.py`: recebe iteravel de `Conta`, faz UMA consulta de `SaldoMensalConta` (`conta__in`) e UMA de `Lancamento` (`conta__in`, com `com_status_in` opcional), agrega em Python, retorna `{conta_id: Decimal}`.

`saldo_do_mes(conta, ano, mes, status_incluidos=None)` vira wrapper: `saldos_do_mes([conta], ...)[conta.pk]`. Assinatura publica preservada — `criar_mes`, `comparativo_meses` e testes existentes nao mudam.

*Por que batch como corpo e escalar como wrapper (e nao o contrario):* o unico caller multi-conta (`resumo_consolidado`) precisa do batch sem N+1; wrapper escalar sobre batch e trivial, o inverso reintroduz o loop de consultas.

*Alternativa rejeitada:* `saldos_do_mes` aceitar lancamentos pre-carregados para economizar 1 consulta — vaza detalhe de carregamento pela interface, acopla os dois services ao mesmo queryset. Custo de 1 consulta constante e mais barato que o acoplamento.

### 2. `resumo_consolidado` consome `saldos_do_mes`

Remove `movimento_por_conta` e o fallback inline. Fluxo: contas (1 consulta), lancamentos exibidos com filtros de conta+status (1), `saldos_do_mes` (2: saldos iniciais + lancamentos do mes sem filtro de conta). Total 4, constante.

`contas_ajuste` ainda precisa dos saldos INICIAIS por conta — `saldos_do_mes` retorna saldo final. Para nao duplicar a consulta de `SaldoMensalConta`: `saldos_do_mes` ganha irma `saldos_iniciais_do_mes(contas, ano, mes)`? Nao — interface cresce sem necessidade. Decisao: `resumo_consolidado` mantem sua consulta propria de `SaldoMensalConta` para `contas_ajuste` (fallback `conta.saldo_atual or 0` — que e regra de EXIBICAO do ajuste, nao a regra de saldo encadeado) e usa `saldos_do_mes` para os saldos finais. Total de consultas: contas 1 + exibidos 1 + `SaldoMensalConta` do ajuste 1 + batch 2 = 5. 

Reavaliando: 5 consultas constantes ainda O(1); alternativa de expor saldos iniciais pelo batch economizaria 1 mas engorda o retorno (`{conta_id: (inicial, final)}`). Escolha: retorno rico `dataclass SaldoConta(inicial, final)` em `saldos_do_mes` — um lugar computa, os dois consumos (ajuste e saldo final) saem da mesma chamada, total volta a 4. Interface continua uma funcao.

### 3. Parse na view, `int` no service

View: `conta_param = request.GET.get("conta")`; `conta_id = int(conta_param) if conta_param else None` — unica conversao, mesma superficie de erro de hoje (`ValueError` → 500 em `?conta=abc`, comportamento pre-existente). Service tipa `conta_id: int | None` e so resolve `next((c for c in contas if c.pk == conta_id), None)`.

### 4. Teste de concordancia por conta

`test_saldos_concordam_com_saldo_do_mes` passa a iterar `for conta in (banco, cartao)` e afirmar `resumo.saldo_por_conta`... o `ResumoMes` NAO expoe `saldo_por_conta` — e nao vai expor (interface minima; view nao usa). Concordancia por conta e afirmada via `saldos_do_mes` diretamente (unidade em `meses/tests.py`) + via `resumo_consolidado(conta_id=conta.pk).saldo_total` para CADA conta (nao so banco). Cobre o cenario da spec sem alargar o dataclass.

### 5. Spec delta usa MODIFIED sobre a capability pendente

`resumo-consolidado` ainda nao foi sincronizada para `openspec/specs/` (change origem nao arquivada). O delta MODIFIED aqui pressupoe arquivamento em ordem: primeiro `add-resumo-consolidado-service`, depois esta. Registrado no proposal.

## Risks / Trade-offs

- [+1 consulta na tela principal (3→4)] → constante, sem N+1; pago em troca de dono unico da regra. `assertNumQueries` atualizado pina o novo orcamento.
- [Wrapper `saldo_do_mes` muda perfil de consultas dos callers escalares (2 consultas como antes — `SaldoMensalConta` + lancamentos — sem mudanca real)] → testes de `meses` e `comparativo` cobrem.
- [Duas changes ativas tocando a mesma capability] → ordem de arquivamento documentada; `openspec validate` nas duas.
- [Regra de exibicao do ajuste (`saldo_inicial` com fallback) confundida com a regra de saldo] → `SaldoConta(inicial, final)` deixa explicito que ambas saem de `saldos_do_mes`; fallback definido em um so lugar.

## Migration Plan

1. `saldos_do_mes` + `SaldoConta` em `meses/services.py`; `saldo_do_mes` vira wrapper; testes de unidade batch.
2. `resumo_consolidado` consome `saldos_do_mes`; remove regra inline; docstring corrigida; `assertNumQueries` ajustado.
3. Parse de `conta_id` movido para a view; assinatura do service tipada.
4. Teste de concordancia por conta; suite completa.

Rollback: reverter commit — sem migracao, sem template.

## Open Questions

Nenhuma bloqueante.
