# Lancamentos

## Purpose
Definir estrutura dos lancamentos, tipos suportados e regras de status calculado.

## Requirements

### Requirement: Campos do lancamento
Todo lancamento SHALL possuir: Descricao, Tipo, Data de vencimento, Data de pagamento
(preenchida apenas ao marcar como Pago), Valor, Conta e Status (somente leitura,
calculado pelo sistema). O pagamento de um lancamento SHALL ser sempre integral;
pagamento parcial nao e suportado.

#### Scenario: Criacao de um lancamento simples
- GIVEN uma conta ja cadastrada
- WHEN o usuario registra um lancamento com Descricao, Tipo, Data de vencimento,
  Valor e Conta
- THEN o sistema SHALL criar o lancamento com Status calculado automaticamente
- AND Data de pagamento SHALL permanecer vazia ate o lancamento ser marcado como Pago

### Requirement: Tipos de lancamento suportados
O sistema SHALL suportar os seguintes tipos de lancamento, cada um com uma direcao
fixa (entrada ou saida) e uma regra de propagacao automatica entre meses:

| Tipo                     | Direcao          | Propagacao automatica                |
|--------------------------|------------------|--------------------------------------|
| Recebimento Fixo         | Entrada          | Sim                                  |
| Recebimento Excepcional  | Entrada          | Nao                                  |
| Gasto Fixo               | Saida            | Sim                                  |
| Gasto Variavel           | Saida            | Nao                                  |
| Assinatura               | Saida            | Sim                                  |
| Parcela de Cartao        | Saida            | Sim, ate atingir o total de parcelas |
| Conciliacao              | Entrada ou Saida (conforme o sinal do ajuste) | Nao |
| Aporte (Investimento)    | Entrada          | Nao                                  |
| Resgate (Investimento)   | Saida            | Nao                                  |

Os tipos Aporte e Resgate SHALL ser exclusivos de contas do tipo Investimento. O
tipo Conciliacao SHALL ser gerado apenas automaticamente pelo sistema (nunca
manualmente pelo usuario), ao ajustar o saldo inicial herdado de um mes.

#### Scenario: Recebimento Fixo e propagado automaticamente
- GIVEN um lancamento do tipo Recebimento Fixo no mes atual
- WHEN um novo mes e criado
- THEN o sistema SHALL gerar automaticamente uma copia desse lancamento no novo mes

#### Scenario: Gasto Variavel nao e propagado automaticamente
- GIVEN um lancamento do tipo Gasto Variavel (ex.: IPVA) no mes atual
- WHEN um novo mes e criado
- THEN o sistema SHALL NOT gerar automaticamente uma copia desse lancamento no novo mes

#### Scenario: Recebimento Excepcional pode ser cadastrado em mes futuro
- GIVEN um mes futuro ja criado pelo usuario
- WHEN o usuario cadastra manualmente um Recebimento Excepcional nesse mes
- THEN o sistema SHALL aceitar o lancamento com Status Previsto

#### Scenario: Conciliacao nao pode ser criada manualmente
- GIVEN o usuario esta criando um novo lancamento
- WHEN ele tenta selecionar o tipo Conciliacao manualmente
- THEN o sistema SHALL impedir a selecao, pois esse tipo e gerado apenas pelo sistema

### Requirement: Calculo automatico do status
O sistema SHALL calcular o Status de cada lancamento automaticamente, sem permitir
edicao manual direta, segundo as regras:
- Previsto: a data de vencimento ainda nao chegou, ou e hoje, e o lancamento nao
  foi pago.
- Pendente: o dia seguinte a data de vencimento ja chegou e o lancamento ainda nao
  foi pago.
- Pago: o lancamento possui uma data de pagamento registrada, independentemente da
  data de vencimento.

#### Scenario: Lancamento pago tem status Pago
- GIVEN um lancamento sem data de pagamento registrada
- WHEN o usuario marca o lancamento como pago, informando a data de pagamento
- THEN o sistema SHALL alterar o Status para Pago imediatamente
- AND o Status SHALL permanecer Pago mesmo que a data de vencimento ainda nao
  tenha chegado

#### Scenario: Lancamento no proprio dia do vencimento ainda e Previsto
- GIVEN um lancamento cuja data de vencimento e hoje
- WHEN o lancamento nao possui data de pagamento registrada
- THEN o sistema SHALL exibir o Status como Previsto

#### Scenario: Lancamento vira Pendente no dia seguinte ao vencimento
- GIVEN um lancamento cuja data de vencimento foi ontem
- WHEN o lancamento nao possui data de pagamento registrada
- THEN o sistema SHALL alterar o Status para Pendente automaticamente
