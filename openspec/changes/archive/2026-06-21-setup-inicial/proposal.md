# Proposal: Implementação inicial do sistema de controle financeiro pessoal

## Why
Hoje o controle financeiro é feito de forma manual/dispersa. Esta mudança implementa
a primeira versão do sistema: controle do mês atual, consulta de meses passados e
projeção de até 12 meses futuros, com regras claras de propagação de lançamentos
recorrentes, cálculo de saldo e parcelamento no cartão de crédito.

## What Changes
- Cadastro de contas (Cartão, Banco, Investimento), cada uma com campos e regras de
  saldo/limite próprias.
- Lançamentos financeiros com cálculo automático de status (Previsto/Pendente/Pago)
  e nove tipos com regras de direção e propagação distintas, incluindo o tipo
  Conciliação (gerado automaticamente pelo sistema) e os tipos Aporte/Resgate
  (exclusivos de contas Investimento).
- Compras parceladas em cartão de crédito, com geração automática das parcelas.
- Criação manual de mês com propagação automática de lançamentos recorrentes,
  incluindo cascata de edição (sobrescreve customização futura) e exclusão (remove
  instâncias futuras já criadas).
- Visualizações: Visão de conta, Visão consolidada (Banco/Cartão), Visão de
  patrimônio (Investimento), navegação histórica e comparativo entre meses.

## Impact
- Capabilities afetadas (todas **ADDED**, por ser a implementação inicial):
  `contas`, `lancamentos`, `parcelas`, `meses`, `visualizacao`.
- Stack técnica e decisões de implementação: ver `design.md` nesta mesma change.
- Checklist de implementação: ver `tasks.md` nesta mesma change.
