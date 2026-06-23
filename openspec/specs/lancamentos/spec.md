# Lancamentos

## Purpose
Definir estrutura dos lancamentos, tipos suportados e regras de status calculado.

## Requirements

### Requirement: Campos do lancamento
Todo lancamento SHALL possuir: Descricao, Tipo, Data de vencimento, Data de pagamento
(preenchida apenas ao marcar como Pago), Valor, Conta, Lancamento Vinculado (opcional,
referencia ao lancamento par da mesma operacao financeira) e Status (somente leitura,
calculado pelo sistema). O pagamento de um lancamento SHALL ser sempre integral;
pagamento parcial nao e suportado. Quando houver dados invalidos no formulario de
lancamento, o sistema SHALL retornar erros de validacao ao usuario e SHALL NOT
levantar erro interno por ausencia de relacao `conta` durante a validacao.

#### Scenario: Criacao de um lancamento simples
- GIVEN uma conta ja cadastrada
- WHEN o usuario registra um lancamento com Descricao, Tipo, Data de vencimento,
  Valor e Conta
- THEN o sistema SHALL criar o lancamento com Status calculado automaticamente
- AND Data de pagamento SHALL permanecer vazia ate o lancamento ser marcado como Pago
- AND Lancamento Vinculado SHALL permanecer vazio se nao informado

#### Scenario: Criacao de lancamento com vinculo informado
- GIVEN uma conta ja cadastrada e um lancamento B existente com mesmo valor absoluto
- WHEN o usuario registra um novo lancamento A informando B como lancamento vinculado
- THEN o sistema SHALL criar A com lancamento_vinculado apontando para B
- AND SHALL automaticamente definir B.lancamento_vinculado como A

#### Scenario: Submissao invalida com tipo incompativel nao causa erro interno
- GIVEN uma conta do tipo Banco existente
- WHEN o usuario envia um novo lancamento com tipo APORTE para essa conta
- THEN o sistema SHALL rejeitar a submissao com erro de validacao no formulario
- AND SHALL NOT gerar excecao interna por ausencia de `conta` durante model clean

### Requirement: Tipos de lancamento suportados
O sistema SHALL suportar os seguintes tipos de lancamento, cada um com uma direcao
fixa (entrada ou saida) e uma regra de geracao/propagacao definida:

| Tipo                     | Direcao          | Regra de geracao entre meses                          |
|--------------------------|------------------|--------------------------------------------------------|
| Recebimento Fixo         | Entrada          | Propagado automaticamente na abertura de mes           |
| Recebimento Excepcional  | Entrada          | Nao propagado automaticamente                          |
| Gasto Fixo               | Saida            | Propagado automaticamente na abertura de mes           |
| Gasto Variavel           | Saida            | Nao propagado automaticamente                          |
| Assinatura               | Saida            | Propagado automaticamente na abertura de mes           |
| Parcela de Cartao        | Saida            | Gerado no registro da compra parcelada; sem propagacao |
| Conciliacao              | Entrada ou Saida (conforme o sinal do ajuste) | Nao |
| Aporte (Investimento)    | Entrada          | Nao                                                    |
| Resgate (Investimento)   | Saida            | Nao                                                    |

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

#### Scenario: Parcela de Cartao e gerada no fluxo de compra parcelada
- GIVEN uma compra parcelada e registrada para uma conta Cartao
- WHEN o sistema conclui o registro da compra
- THEN o sistema SHALL gerar os lancamentos de Parcela de Cartao no fluxo da compra
- AND SHALL NOT depender da abertura de novo mes para gerar essas parcelas

#### Scenario: Recebimento Excepcional pode ser cadastrado em mes futuro
- GIVEN um mes futuro ja criado pelo usuario
- WHEN o usuario cadastra manualmente um Recebimento Excepcional nesse mes
- THEN o sistema SHALL aceitar o lancamento com Status Previsto

#### Scenario: Conciliacao nao pode ser criada manualmente
- GIVEN o usuario esta criando um novo lancamento
- WHEN ele tenta selecionar o tipo Conciliacao manualmente
- THEN o sistema SHALL impedir a selecao, pois esse tipo e gerado apenas pelo sistema

### Requirement: Parcela de Cartao nao participa de cascata de recorrencia
O sistema SHALL aplicar cascata de edicao/exclusao de serie recorrente apenas aos
tipos recorrentes propagados na abertura de mes. Lancamentos do tipo Parcela de
Cartao SHALL NOT participar dessa cascata como serie recorrente.

#### Scenario: Edicao de uma parcela nao atualiza parcelas futuras em massa
- GIVEN existem varias parcelas de uma mesma compra em meses futuros
- WHEN o usuario edita manualmente uma unica parcela
- THEN o sistema SHALL aplicar a alteracao somente a parcela editada

#### Scenario: Exclusao de uma parcela nao remove parcelas futuras em massa
- GIVEN existem varias parcelas de uma mesma compra em meses futuros
- WHEN o usuario exclui uma unica parcela
- THEN o sistema SHALL remover somente a parcela selecionada

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

### Requirement: Restricao de tipos especiais no cadastro manual
No cadastro manual de lancamentos, o sistema SHALL impedir selecao dos tipos
`Conciliacao` e `Parcela de Cartao`, pois esses tipos sao gerados por fluxos
especificos do sistema.

#### Scenario: Usuario tenta criar Conciliacao manualmente
- **WHEN** o usuario abre o formulario de novo lancamento manual
- **THEN** o sistema SHALL nao disponibilizar o tipo Conciliacao para selecao

#### Scenario: Usuario tenta criar Parcela de Cartao manualmente
- **WHEN** o usuario abre o formulario de novo lancamento manual
- **THEN** o sistema SHALL nao disponibilizar o tipo Parcela de Cartao para selecao
- **AND** SHALL orientar uso do fluxo de compra parcelada para gerar parcelas

### Requirement: Consistencia entre filtro de status e calculo de saldo
Quando o usuario aplicar filtros de status na tela mensal, o sistema SHALL usar os
mesmos criterios de status para listagem de lancamentos e para calculo de saldo
exibido, sem divergencia entre os dois resultados.

#### Scenario: Filtro por status gera lista e saldo coerentes
- **WHEN** o usuario seleciona apenas status Pago e Previsto
- **THEN** o sistema SHALL exibir somente lancamentos desses status
- **AND** SHALL calcular o saldo exibido com base no mesmo subconjunto de lancamentos
