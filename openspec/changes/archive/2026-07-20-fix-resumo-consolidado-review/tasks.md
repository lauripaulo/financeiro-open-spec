# Tasks: fix-resumo-consolidado-review

## 1. Batch saldos_do_mes em meses

- [x] 1.1 Criar dataclass congelada `SaldoConta(inicial, final)` e funcao `saldos_do_mes(contas, ano, mes, status_incluidos=None)` em `meses/services.py`: uma consulta de `SaldoMensalConta` (`conta__in`) + uma de `Lancamento` (`conta__in`, `com_status_in` opcional), retorna `{conta_id: SaldoConta}`
- [x] 1.2 Reescrever `saldo_do_mes(conta, ano, mes, status_incluidos=None)` como wrapper: `saldos_do_mes([conta], ...)[conta.pk].final` — assinatura e retorno preservados
- [x] 1.3 Testes em `meses/tests.py`: batch com multiplas contas (fallback `saldo_atual`, filtro de status) e concordancia batch == wrapper escalar por conta

## 2. resumo_consolidado consome o batch

- [x] 2.1 Remover de `visualizacao/services.py` a regra inline (`movimento_por_conta`, fallback e consulta propria de `SaldoMensalConta`); obter `{conta_id: SaldoConta}` via `saldos_do_mes` e derivar `contas_ajuste` (inicial) e `saldo_por_conta` (final) da mesma chamada
- [x] 2.2 Corrigir docstring com o orcamento real de consultas; atualizar `test_passada_unica_tres_consultas` para o novo numero constante (renomear coerentemente)

## 3. Parse de conta_id na view

- [x] 3.1 `visao_consolidada` converte `request.GET.get("conta")` para `int` uma unica vez e passa `conta_id: int | None` ao service; service deixa de chamar `int()`
- [x] 3.2 Ajustar testes do service que passavam `conta_id` como string para passar `int`

## 4. Concordancia por conta

- [x] 4.1 Reescrever `test_saldos_concordam_com_saldo_do_mes`: para CADA conta (banco e cartao), `resumo_consolidado(ano, mes, conta_id=conta.pk, status=...).saldo_total == saldo_do_mes(conta, ...)`, com `status` em `None`, `["PAGO"]` e `["PREVISTO", "PENDENTE"]`

## 5. Encerramento

- [x] 5.1 Suite completa (`manage.py test`) verde; grep confirmando que agregacao de saldo final so existe em `meses/services.py`
- [x] 5.2 `openspec validate --changes` nas duas changes ativas; registrar ordem de arquivamento (primeiro `add-resumo-consolidado-service`, depois esta)
