## MODIFIED Requirements

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
| Transferencia Enviada    | Saida            | Nao; gerado pelo fluxo de transferencia                |
| Transferencia Recebida   | Entrada          | Nao; gerado pelo fluxo de transferencia                |

Os tipos Aporte e Resgate SHALL ser exclusivos de contas do tipo Investimento. Os
tipos Transferencia Enviada e Transferencia Recebida SHALL ser exclusivos de contas
do tipo Banco ou Cartao. O tipo Conciliacao SHALL ser gerado apenas automaticamente
pelo sistema (nunca manualmente pelo usuario), ao ajustar o saldo inicial herdado de
um mes.

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

#### Scenario: Transferencia Enviada nao e propagada na abertura de mes
- GIVEN um lancamento do tipo Transferencia Enviada no mes atual
- WHEN um novo mes e criado
- THEN o sistema SHALL NOT gerar automaticamente uma copia desse lancamento no novo mes

### Requirement: Restricao de tipos especiais no cadastro manual
No cadastro manual de lancamentos, o sistema SHALL impedir selecao dos tipos
`Conciliacao`, `Parcela de Cartao`, `Transferencia Enviada` e `Transferencia Recebida`,
pois esses tipos sao gerados por fluxos especificos do sistema. Contudo, ao editar um
lancamento existente desses tipos, o sistema SHALL permitir a edicao de seus outros
campos, desabilitando o campo tipo para garantir que permaneca inalterado.

#### Scenario: Usuario tenta criar Conciliacao manualmente
- **WHEN** o usuario abre o formulario de novo lancamento manual
- **THEN** o sistema SHALL nao disponibilizar o tipo Conciliacao para selecao

#### Scenario: Usuario tenta criar Parcela de Cartao manualmente
- **WHEN** o usuario abre o formulario de novo lancamento manual
- **THEN** o sistema SHALL nao disponibilizar o tipo Parcela de Cartao para selecao
- **AND** SHALL orientar uso do fluxo de compra parcelada para gerar parcelas

#### Scenario: Usuario tenta criar Transferencia Enviada ou Recebida manualmente
- **WHEN** o usuario abre o formulario de novo lancamento manual
- **THEN** o sistema SHALL nao disponibilizar os tipos Transferencia Enviada nem
  Transferencia Recebida para selecao
- **AND** SHALL orientar uso do fluxo de transferencia para registrar essas operacoes

#### Scenario: Usuario edita Parcela de Cartao existente
- **WHEN** o usuario abre a edicao de um lancamento existente do tipo Parcela de Cartao
- **THEN** o sistema SHALL disponibilizar o tipo Parcela de Cartao no formulario
- **AND** SHALL desabilitar a alteracao do campo tipo
