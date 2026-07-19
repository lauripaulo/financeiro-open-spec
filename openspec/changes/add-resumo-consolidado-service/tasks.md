# Tasks: add-resumo-consolidado-service

## 1. Service resumo_consolidado

- [ ] 1.1 Criar `visualizacao/services.py` com dataclass congelada `ResumoMes` (lancamentos, total_entradas, total_saidas, saldo_total, contas_ajuste, alertas_limite)
- [ ] 1.2 Implementar `resumo_consolidado(ano, mes, conta_id=None, status=None)`: queryset de lancamentos identico ao da view atual (contas Banco/Cartao, `select_related`, `order_by("data_vencimento", "id")`, filtros de conta e status via `com_status_in`)
- [ ] 1.3 Buscar `SaldoMensalConta` do mes em consulta unica (`conta__in`) com fallback `conta.saldo_atual or Decimal("0.00")` por conta; montar `contas_ajuste`
- [ ] 1.4 Computar em passada unica: totais de entradas/saidas da lista exibida, saldo por conta (lancamentos do mes sem filtro de conta, com filtro de status), saldo total (conta filtrada ou soma de todas) e alertas de limite negativo das contas Banco reutilizando o saldo ja computado

## 2. Testes do service

- [ ] 2.1 Testes diretos de `resumo_consolidado`: resumo basico, filtro por conta, filtro por status, exclusao de contas Investimento, alertas com filtro de conta ativo (sem client HTTP)
- [ ] 2.2 Teste de concordancia: saldo por conta do resumo == `saldo_do_mes(conta, ano, mes, status_incluidos=status)` com e sem filtro de status
- [ ] 2.3 Teste de consulta unica: `assertNumQueries` (ou equivalente) cobrindo que `SaldoMensalConta` e consultada uma vez

## 3. Troca da view

- [ ] 3.1 Reescrever `visao_consolidada` como camada fina: parse de filtros, gate de mes nao criado, chamada ao service, navegacao de mes, pop de `aviso_limite_meses`, render — sem loops de agregacao nem queries de `SaldoMensalConta`
- [ ] 3.2 Rodar suite completa (`manage.py test`) e confirmar que os testes existentes da view consolidada passam sem alteracao de comportamento

## 4. Unificar regra de saldo

- [ ] 4.1 Apontar `criar_mes` (meses/services.py:121) para `saldo_do_mes(conta, ano_anterior, mes_anterior)`
- [ ] 4.2 Deletar `_saldo_final_periodo` de `meses/services.py`
- [ ] 4.3 Rodar suite completa; conferir testes de encadeamento de saldo e abertura sequencial de meses em `meses/tests.py`

## 5. Encerramento

- [ ] 5.1 Verificar que nenhuma copia inline da regra de saldo sobrevive (`grep` por `saldo_inicial` fora de meses/services e do service novo)
- [ ] 5.2 `openspec validate --changes` e revisao final dos artefatos
