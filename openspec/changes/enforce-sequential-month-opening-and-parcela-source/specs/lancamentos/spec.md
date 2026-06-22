# Delta para Lancamentos

## REQUISITOS MODIFICADOS

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

## REQUISITOS ADICIONADOS

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
