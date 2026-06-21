# Delta for Parcelas

## ADDED Requirements

### Requirement: Geração automática de lançamentos de parcela
O sistema SHALL criar automaticamente um lançamento do tipo Parcela de Cartão para cada parcela de uma compra parcelada registrada em conta do tipo Cartão, com vencimentos a partir do mês seguinte ao da compra, usando o dia de vencimento configurado na conta Cartão associada.

#### Scenario: Compra parcelada em 10x
- GIVEN uma conta do tipo Cartão já cadastrada com vencimento no dia 10
- WHEN o usuário registra uma compra de R$ 100,00 em janeiro, parcelada em 10x
- THEN o sistema SHALL criar 10 lançamentos do tipo Parcela de Cartão de R$ 10,00 cada
- AND os vencimentos SHALL ir de 10/fevereiro a 10/novembro

### Requirement: Campos adicionais da parcela
Todo lançamento do tipo Parcela de Cartão SHALL possuir, além dos campos comuns de
lançamento, o Total de parcelas e o número da Parcela atual.

#### Scenario: Consulta de progresso de uma parcela
- GIVEN uma compra parcelada em 10x
- WHEN o usuário visualiza a 3ª parcela
- THEN o sistema SHALL exibir Total de parcelas = 10 e Parcela atual = 3

### Requirement: Descrição com indicação de progresso
O sistema SHALL gerar automaticamente a descrição de cada parcela no formato
"<descrição da compra> <parcela atual>/<total de parcelas>".

#### Scenario: Descrição de parcela individual
- GIVEN uma compra de notebook parcelada em 10x
- WHEN o sistema gera o lançamento da segunda parcela
- THEN a Descrição SHALL ser "Compra de notebook 2/10"

### Requirement: Pagamento de fatura é manual e independente
O sistema SHALL tratar o pagamento da fatura do Cartão como um lançamento manual e
independente, registrado pelo usuário. O sistema SHALL NOT gerar automaticamente
uma saída vinculada em nenhuma conta Banco quando uma fatura é paga.

#### Scenario: Usuário paga a fatura do cartão
- GIVEN uma conta Cartão com parcelas previstas no mês
- WHEN o usuário quer refletir a saída do dinheiro de sua conta corrente
- THEN ele SHALL cadastrar manualmente um lançamento de saída na conta Banco
  correspondente, sem nenhuma geração automática pelo sistema
