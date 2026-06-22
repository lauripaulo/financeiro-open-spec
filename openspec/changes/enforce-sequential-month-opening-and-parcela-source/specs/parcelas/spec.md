# Delta for Parcelas

## MODIFIED Requirements

### Requirement: Geracao automatica de lancamentos de parcela
O sistema SHALL criar automaticamente um lancamento do tipo Parcela de Cartao para
cada parcela de uma compra parcelada registrada em conta do tipo Cartao, com
vencimentos a partir do mes seguinte ao da compra, usando o dia de vencimento
configurado na conta Cartao associada. Essa geracao SHALL ocorrer no momento do
registro da compra parcelada, e SHALL produzir toda a serie de parcelas prevista.

#### Scenario: Compra parcelada em 10x
- GIVEN uma conta do tipo Cartao ja cadastrada com vencimento no dia 10
- WHEN o usuario registra uma compra de R$ 100,00 em janeiro, parcelada em 10x
- THEN o sistema SHALL criar 10 lancamentos do tipo Parcela de Cartao de R$ 10,00 cada
- AND os vencimentos SHALL ir de 10/fevereiro a 10/novembro

## ADDED Requirements

### Requirement: Abertura de mes nao gera parcelas de cartao
O sistema SHALL NOT gerar lancamentos do tipo Parcela de Cartao durante o fluxo de
abertura/criacao de mes. A origem dessas parcelas SHALL ser exclusivamente o fluxo
de compra parcelada.

#### Scenario: Mes aberto apos compra parcelada
- GIVEN uma compra parcelada ja foi registrada e suas parcelas foram geradas
- WHEN o usuario abre um novo mes na sequencia
- THEN o sistema SHALL nao criar parcelas adicionais dessa compra por abertura de mes
