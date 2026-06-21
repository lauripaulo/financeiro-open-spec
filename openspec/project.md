# Project Context

## Purpose
Sistema de controle financeiro pessoal. Permite controlar os gastos do mês atual,
consultar meses passados e projetar até 12 meses futuros (contas, recebimentos,
parcelas e assinaturas), com saldo calculado por conta e por mês.

## Domains
- **contas** — Cadastro e regras das contas financeiras (Cartão, Banco, Investimento).
- **lancamentos** — Entradas e saídas financeiras, seus tipos e ciclo de status.
- **parcelas** — Compras parceladas associadas a contas do tipo Cartão.
- **meses** — Criação, propagação automática de lançamentos e cálculo de saldo de cada mês.
- **visualizacao** — Visão de conta, visão consolidada, visão de patrimônio (Investimento),
  navegação histórica e comparação entre meses.

## Tech Stack
- Backend: Python + Django.
- Banco de dados: SQLite (uso pessoal/familiar).
- Frontend: Django templates + HTMX.
- Deploy: Docker, no mesmo NAS que já hospeda outros serviços do usuário.

Ver `changes/setup-inicial/design.md` para o detalhamento dessas decisões técnicas.

## Conventions
- Valores monetários SHALL ser representados em Reais (R$), com duas casas decimais.
- Toda referência a "mês" SHALL incluir o ano (mês/ano), nunca apenas o mês.
- Status de lançamento (Previsto / Pendente / Pago) é sempre calculado pelo sistema;
  NUNCA é um campo editável diretamente pelo usuário.
- Pagamento de lançamento é sempre integral; pagamento parcial está fora de escopo.

## Decisions Log
1. **Limite da conta Banco** — o sistema apenas alerta; nunca bloqueia uma ação por
   causa do limite negativo.
2. **Conta Cartão** — não possui campo de limite de crédito; fora de escopo desta versão.
3. **Primeiro mês** — é criado sem lançamentos, mas herda o saldo informado nas contas
   Banco e Investimento no momento da criação (não é um saldo zerado).
4. **Conta Investimento** — usa tipos de lançamento dedicados (Aporte / Resgate); seu
   saldo é tratado separadamente e não entra no saldo consolidado mensal de Banco/Cartão.
5. **Pagamento de fatura do Cartão** — é um lançamento manual e independente; o sistema
   não gera automaticamente uma saída vinculada na conta Banco.
6. **Edição de lançamento recorrente** — a alteração é aplicada a todas as instâncias já
   criadas em meses futuros, mesmo que alguma já tenha sido customizada manualmente
   (a edição em massa sobrescreve a customização).
7. **Exclusão de lançamento recorrente** — remove também as instâncias já criadas em
   meses futuros, além de interromper novas propagações.
8. **Transição de status Previsto → Pendente** — ocorre a partir do dia seguinte à data
   de vencimento, não no próprio dia.
9. **Limite de 12 meses futuros** — é um limite "soft": o sistema permite criar além
   dele, mas exibe um aviso ao usuário.
10. **Pagamento parcial** — fora de escopo; o pagamento de um lançamento é sempre integral.
