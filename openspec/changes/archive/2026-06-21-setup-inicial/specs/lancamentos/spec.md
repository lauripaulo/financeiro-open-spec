# Delta for Lançamentos

## ADDED Requirements

### Requirement: Campos do lançamento
Todo lançamento SHALL possuir: Descrição, Tipo, Data de vencimento, Data de pagamento
(preenchida apenas ao marcar como Pago), Valor, Conta e Status (somente leitura,
calculado pelo sistema). O pagamento de um lançamento SHALL ser sempre integral;
pagamento parcial não é suportado.

#### Scenario: Criação de um lançamento simples
- GIVEN uma conta já cadastrada
- WHEN o usuário registra um lançamento com Descrição, Tipo, Data de vencimento,
  Valor e Conta
- THEN o sistema SHALL criar o lançamento com Status calculado automaticamente
- AND Data de pagamento SHALL permanecer vazia até o lançamento ser marcado como Pago

### Requirement: Tipos de lançamento suportados
O sistema SHALL suportar os seguintes tipos de lançamento, cada um com uma direção
fixa (entrada ou saída) e uma regra de propagação automática entre meses:

| Tipo                     | Direção          | Propagação automática            |
|--------------------------|------------------|-----------------------------------|
| Recebimento Fixo         | Entrada          | Sim                                |
| Recebimento Excepcional  | Entrada          | Não                                |
| Gasto Fixo               | Saída            | Sim                                |
| Gasto Variável           | Saída            | Não                                |
| Assinatura               | Saída            | Sim                                |
| Parcela de Cartão        | Saída            | Sim, até atingir o total de parcelas |
| Conciliação              | Entrada ou Saída (conforme o sinal do ajuste) | Não |
| Aporte (Investimento)    | Entrada          | Não                                |
| Resgate (Investimento)   | Saída            | Não                                |

Os tipos Aporte e Resgate SHALL ser exclusivos de contas do tipo Investimento. O
tipo Conciliação SHALL ser gerado apenas automaticamente pelo sistema (nunca
manualmente pelo usuário), ao ajustar o saldo inicial herdado de um mês.

#### Scenario: Recebimento Fixo é propagado automaticamente
- GIVEN um lançamento do tipo Recebimento Fixo no mês atual
- WHEN um novo mês é criado
- THEN o sistema SHALL gerar automaticamente uma cópia desse lançamento no novo mês

#### Scenario: Gasto Variável não é propagado automaticamente
- GIVEN um lançamento do tipo Gasto Variável (ex.: IPVA) no mês atual
- WHEN um novo mês é criado
- THEN o sistema SHALL NOT gerar automaticamente uma cópia desse lançamento no novo mês

#### Scenario: Recebimento Excepcional pode ser cadastrado em mês futuro
- GIVEN um mês futuro já criado pelo usuário
- WHEN o usuário cadastra manualmente um Recebimento Excepcional nesse mês
- THEN o sistema SHALL aceitar o lançamento com Status Previsto

#### Scenario: Conciliação não pode ser criada manualmente
- GIVEN o usuário está criando um novo lançamento
- WHEN ele tenta selecionar o tipo Conciliação manualmente
- THEN o sistema SHALL impedir a seleção, pois esse tipo é gerado apenas pelo sistema

### Requirement: Cálculo automático do status
O sistema SHALL calcular o Status de cada lançamento automaticamente, sem permitir
edição manual direta, segundo as regras:
- Previsto: a data de vencimento ainda não chegou, ou é hoje, e o lançamento não
  foi pago.
- Pendente: o dia seguinte à data de vencimento já chegou e o lançamento ainda não
  foi pago.
- Pago: o lançamento possui uma data de pagamento registrada, independentemente da
  data de vencimento.

#### Scenario: Lançamento pago tem status Pago
- GIVEN um lançamento sem data de pagamento registrada
- WHEN o usuário marca o lançamento como pago, informando a data de pagamento
- THEN o sistema SHALL alterar o Status para Pago imediatamente
- AND o Status SHALL permanecer Pago mesmo que a data de vencimento ainda não
  tenha chegado

#### Scenario: Lançamento no próprio dia do vencimento ainda é Previsto
- GIVEN um lançamento cuja data de vencimento é hoje
- WHEN o lançamento não possui data de pagamento registrada
- THEN o sistema SHALL exibir o Status como Previsto

#### Scenario: Lançamento vira Pendente no dia seguinte ao vencimento
- GIVEN um lançamento cuja data de vencimento foi ontem
- WHEN o lançamento não possui data de pagamento registrada
- THEN o sistema SHALL alterar o Status para Pendente automaticamente
