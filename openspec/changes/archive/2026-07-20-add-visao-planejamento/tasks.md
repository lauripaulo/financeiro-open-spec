## 1. Funções de Serviço (meses/services.py)

- [x] 1.1 Implementar `saldo_real_em_data(conta, data)`: âncora SaldoMensalConta do mês + pagos do mês até data
- [x] 1.2 Implementar `saldo_projetado_em_data(conta, data)`: mesma âncora + pagos e planejados/pendentes com vencimento até data
- [x] 1.3 Implementar `total_gastos_cartao_por_mes(contas_cartao)`: retorna dict `{(ano, mes): {conta_id: Decimal}}` para mês atual + até 3 futuros abertos

## 2. Serviço de Planejamento (visualizacao/services.py)

- [x] 2.1 Criar dataclass `SaldoBanco` com campos `conta`, `saldo_real`, `saldo_projetado`
- [x] 2.2 Criar dataclass `FaturaCartao` com campos `conta` e `faturas` (lista de `{ano, mes, total}`)
- [x] 2.3 Criar dataclass `SaldoInvestimento` com campos `conta`, `saldo`
- [x] 2.4 Criar dataclass `ResumoPlajamento` agregando listas dos três tipos + totais + meses_cartao
- [x] 2.5 Implementar função `planejamento_financeiro(data_ref)` que computa o ResumoPlajamento completo

## 3. View e URL (visualizacao/)

- [x] 3.1 Implementar view `visao_planejamento(request)` com parse de `?data=` (default hoje), fallback para último mês aberto se mês não aberto
- [x] 3.2 Adicionar path `planejamento/` em `visualizacao/urls.py`

## 4. Template

- [x] 4.1 Criar `templates/visualizacao/planejamento.html` com seções Banco, Cartão, Investimento e date picker
- [x] 4.2 Adicionar link "Planejamento" na navbar em `templates/base.html`

## 5. Testes

- [x] 5.1 Testes para `saldo_real_em_data`: sem pagamentos, com pagamentos parciais, com SaldoMensalConta ausente (fallback)
- [x] 5.2 Testes para `saldo_projetado_em_data`: só pagos, pagos + previstos, só previstos
- [x] 5.3 Testes para `total_gastos_cartao_por_mes`: mês atual, múltiplos meses, limite de 4 meses
- [x] 5.4 Teste de view: GET `/planejamento/` retorna 200, contexto correto, fallback sem meses abertos
