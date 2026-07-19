# Design: add-resumo-consolidado-service

## Context

`visao_consolidada` (visualizacao/views.py:57-156) e uma view de ~100 linhas que mistura dispatch HTTP com toda a logica de consolidacao do mes: filtragem de lancamentos, loop de entradas/saidas, loop de saldo por conta, loop de saldo inicial com fallback, loop de alertas de limite (que recomputa saldo), navegacao de mes e pop de aviso de sessao. `visualizacao` e o unico app sem `services.py`, contrariando a arquitetura declarada em CLAUDE.md e arquitetura.md.

A regra de saldo mensal existe em 3 copias:

1. `_saldo_final_periodo` (meses/services.py:31-46) — usada so por `criar_mes` na linha 121; identica a `saldo_do_mes` com `status_incluidos=None`.
2. `saldo_do_mes` (meses/services.py:244-263) — a implementacao canonica, com filtro opcional de status.
3. Loops inline em `visao_consolidada` (views.py:91-97, 108-120) — totais e fallback de `saldo_inicial` re-encodados.

A view chama `saldo_do_mes` por conta duas vezes (saldo total nas linhas 101-106 e alertas nas linhas 122-128) e faz uma query `SaldoMensalConta` por conta no loop de `contas_ajuste` (N+1).

Restricoes: valores monetarios em `Decimal`; status e computado (nunca armazenado); contas `Investimento` ficam fora da consolidada; comportamento observavel do usuario nao pode mudar.

## Goals / Non-Goals

**Goals:**

- Criar a seam `visualizacao/services.py` com `resumo_consolidado(...)` retornando um value object; view vira dispatch + render.
- Uma unica implementacao da regra de saldo mensal no sistema (`saldo_do_mes`); deletar `_saldo_final_periodo`.
- Eliminar o recomputo duplo de saldo por conta e o N+1 de `SaldoMensalConta` na tela principal.
- Logica de consolidacao testavel diretamente, sem client HTTP.

**Non-Goals:**

- Mudar comportamento, template ou contexto renderizado da tela consolidada.
- Refatorar `comparativo_meses`, `visao_patrimonio` ou outras views de `visualizacao` (candidatos futuros).
- Mexer no protocolo de sessao `aviso_limite_meses` (candidato 7 da revisao de arquitetura, fora de escopo).
- Mudar `criar_mes` alem da troca `_saldo_final_periodo` → `saldo_do_mes`.
- Migracao de dados ou mudanca de modelos.

## Decisions

### 1. Value object `ResumoMes` como retorno do service

`@dataclass(frozen=True)` com campos: `lancamentos` (lista), `total_entradas`, `total_saidas`, `saldo_total`, `contas_ajuste` (lista de `(conta, saldo_inicial)` ou dataclass `ContaAjuste`), `alertas_limite` (lista de strings).

*Por que:* a view so injeta campos no contexto do template; um dict funcionaria, mas dataclass documenta o contrato e falha rapido em typo. *Alternativa considerada:* retornar dict — rejeitada por interface implicita.

*Nota:* mensagens de alerta ficam como strings prontas ("{nome}: limite negativo ultrapassado.") para nao mudar o template. Se o template precisar de estrutura no futuro, o alerta vira value object — fora de escopo agora.

### 2. Passada unica sobre os dados

`resumo_consolidado` busca uma vez: os lancamentos filtrados (com `select_related` atual), todos os `SaldoMensalConta` do mes em uma query (`conta__in=contas_base`, dict por `conta_id`), e computa saldo por conta somando lancamentos por conta em Python sobre a lista ja carregada. Totais de entradas/saidas, saldo total, saldos por conta e alertas saem da mesma passada.

*Por que:* mata o N+1 (uma query de `SaldoMensalConta` em vez de uma por conta) e o recomputo (hoje `saldo_do_mes` roda 2x por conta — queries de lancamentos por conta, duas vezes).

*Cuidado:* o saldo por conta para alertas/saldo_total considera lancamentos da conta no mes respeitando o filtro de status — mas NAO o filtro de `conta_id` (alertas cobrem todas as contas Banco mesmo com filtro de conta ativo, comportamento atual). Isso exige duas colecoes: lancamentos filtrados para exibicao (com filtro de conta) e lancamentos do mes para saldos (sem filtro de conta, com filtro de status). Comportamento atual preservado exatamente.

### 3. `saldo_do_mes` permanece a implementacao canonica; passada unica e otimizacao interna do service

A regra de saldo (saldo_inicial com fallback + entradas − saidas) fica definida em `saldo_do_mes`. O service replica o resultado em passada unica — para garantir que nao divirja, um teste de concordancia afirma `resumo por conta == saldo_do_mes(conta, ...)` para cada conta em cenarios com e sem filtro de status.

*Por que nao chamar `saldo_do_mes` por conta dentro do service:* reintroduz o N+1 que queremos matar. *Por que nao mover a agregacao para SQL (Sum condicional):* status e computado em Python (`property status`); filtro de status ja materializa a lista. Ganho marginal, risco de divergencia Python/SQL — rejeitado por ora.

*Alternativa considerada:* dar a `saldo_do_mes` um modo batch (`saldos_do_mes(contas, ...)`). Adiado — interface de `meses` nao precisa crescer para servir um caller.

### 4. `_saldo_final_periodo` deletada; `criar_mes` chama `saldo_do_mes`

Teste de delecao da revisao de arquitetura: `_saldo_final_periodo(conta, ano, mes) == saldo_do_mes(conta, ano, mes, status_incluidos=None)` — copia identica. `criar_mes` (meses/services.py:121) passa a chamar `saldo_do_mes(conta, ano_anterior, mes_anterior)`.

*Por que:* 5 pontos de edicao para uma regra viram 1. Sem mudanca de comportamento: assinaturas equivalentes, mesmo resultado.

### 5. View vira dispatch puro

`visao_consolidada` mantem: parse de filtros (`_filtros_mes`, `_parse_status`, `conta_id`), gate de mes nao criado, chamada `resumo_consolidado(ano, mes, conta_id, status)`, navegacao de mes, pop de `aviso_limite_meses` da sessao, render. Tudo que e HTTP/sessao fica na view; tudo que e dominio vai para o service.

*Por que sessao fica na view:* `request.session` e concern HTTP; o service nao deve conhecer request. O protocolo de sessao e alvo do candidato 7, nao deste.

## Risks / Trade-offs

- [Passada unica divergir de `saldo_do_mes`] → teste de concordancia por conta com/sem filtro de status; testes HTTP existentes (~41) como rede de regressao.
- [Diferenca sutil de ordenacao/filtragem na lista exibida] → manter exatamente o queryset atual (`select_related`, `order_by("data_vencimento", "id")`, `com_status_in`); comparar contexto renderizado nos testes existentes.
- [`criar_mes` mudar de comportamento com a troca de funcao] → as duas funcoes sao caractere a caractere equivalentes no caso `status=None`; testes de encadeamento de saldo em `meses/tests.py` cobrem.
- [Escopo crescer para os outros candidatos da revisao] → non-goals explicitos; candidatos 3-8 ficam para mudancas futuras.

## Migration Plan

Puramente aditivo ate o passo final:

1. Criar `visualizacao/services.py` com `resumo_consolidado` + testes de service (incluindo concordancia com `saldo_do_mes`).
2. Trocar a view para consumir o service; rodar suite completa.
3. Deletar `_saldo_final_periodo`; apontar `criar_mes` para `saldo_do_mes`; rodar suite.

Rollback: reverter o commit — sem migracao de dados, sem mudanca de schema ou template.

## Open Questions

Nenhuma bloqueante. Nome do value object (`ResumoMes` vs `ResumoConsolidado`) decidido na implementacao — preferencia por `ResumoMes` (curto, dominio em portugues).
