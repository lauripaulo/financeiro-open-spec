## Context

O sistema financeiro usa um modelo de competência mensal (`MesAberto`, `SaldoMensalConta`, `Lancamento`). O saldo de qualquer conta é calculado por `saldo_do_mes()` que soma todos os lançamentos do mês independente de `data_pagamento`. Não existe visão de saldo em data arbitrária nem separação entre "o que já aconteceu" e "o que está planejado".

O campo `Conta.saldo_atual` é uma semente usada apenas no primeiro mês aberto; após isso, o saldo se propaga via `SaldoMensalConta`. A função `saldo_investimento()` já existe e calcula corretamente o saldo acumulado de investimentos.

## Goals / Non-Goals

**Goals:**
- Calcular saldo real (apenas pagos) e projetado (pagos + planejados até data) para contas Banco
- Calcular total de gastos por fatura para contas Cartão (mês atual + até 3 futuros abertos)
- Exibir saldo real de investimentos (reusar função existente)
- Nova tela `/planejamento/` na navbar com date picker para data de referência
- Zero migrations: implementação puramente em camada de serviço e view

**Non-Goals:**
- Projeção além de meses já abertos (sem inferência de recorrentes em meses futuros)
- Histórico retroativo / comparativo por período
- Alertas ou notificações baseados em saldo projetado
- Modificação de qualquer modelo de dados existente

## Decisions

### Âncora do saldo (Opção B)

Âncora = `SaldoMensalConta(mês da data de referência).saldo_inicial`.

Essa âncora representa o saldo contábil herdado de todos os meses anteriores, incluindo lançamentos pendentes. O usuário pode corrigi-la via fluxo de Conciliação já existente. Fallback para `conta.saldo_atual` se `SaldoMensalConta` não existir para o mês.

**Alternativa rejeitada:** usar `conta.saldo_atual` diretamente como âncora — mais simples, mas imutável após o cadastro, sem mecanismo de correção.

### Saldo Real vs Projetado

```
saldo_real(conta, data D):
    âncora = SaldoMensalConta(ano=D.year, mes=D.month).saldo_inicial
    + SOMA(lançamentos do mês D onde data_pagamento IS NOT NULL AND data_pagamento <= D)

saldo_projetado(conta, data D):
    âncora = SaldoMensalConta(ano=D.year, mes=D.month).saldo_inicial
    + SOMA(lançamentos do mês D onde data_pagamento <= D
           OU (data_pagamento IS NULL AND data_vencimento <= D))
```

Ambos restringem ao `competencia_mes` da data de referência. O saldo_inicial já encapsula todos os meses anteriores.

### Cartão — Fatura por Mês

```
total_gastos_cartao_por_mes(contas_cartao):
    meses = MesAberto[atual até atual+3] (máximo 4 meses)
    para cada mes: soma de SAÍDAS de todas as contas cartão nesse mês
    retorna {(ano, mes): {conta_id: Decimal}}
```

Inclui lançamentos de qualquer status (pagos ou não) — mostra o total da fatura, não o saldo residual.

### Date picker — limite de meses

Se a data de referência cair em mês não aberto: exibir aviso e usar o último mês aberto como proxy. A UI deve deixar claro que o saldo projetado é limitado aos meses abertos.

### Sem batch adicional para investimentos

`saldo_investimento(conta)` já existe em `meses/services.py`. A view chama diretamente para cada conta investimento.

## Risks / Trade-offs

- **Saldo_inicial não é caixa puro:** a âncora inclui pendentes de meses anteriores. Aceitável porque o fluxo de Conciliação já existe para correção. Documentado na UI com nota explicativa.
- **Data fora do mês aberto:** se a data escolhida está num mês não aberto, usa o último mês aberto. Comportamento defensivo, não erro.
- **Performance:** para cada conta banco, 1 query no `SaldoMensalConta` + 1 query no `Lancamento`. Para N contas banco, 2N queries. Aceitável para o volume típico (< 10 contas).
