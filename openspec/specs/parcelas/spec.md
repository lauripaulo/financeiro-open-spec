# Parcelas

## Purpose
Definir regras para compras parceladas em cartao e geracao automatica de parcelas.

## Requirements

### Requirement: Geracao automatica de lancamentos de parcela
O sistema SHALL criar automaticamente um lancamento do tipo Parcela de Cartao para cada parcela de uma compra parcelada registrada em conta do tipo Cartao, com vencimentos a partir do mes seguinte ao da compra, usando o dia de vencimento configurado na conta Cartao associada.

#### Scenario: Compra parcelada em 10x
- GIVEN uma conta do tipo Cartao ja cadastrada com vencimento no dia 10
- WHEN o usuario registra uma compra de R$ 100,00 em janeiro, parcelada em 10x
- THEN o sistema SHALL criar 10 lancamentos do tipo Parcela de Cartao de R$ 10,00 cada
- AND os vencimentos SHALL ir de 10/fevereiro a 10/novembro

### Requirement: Campos adicionais da parcela
Todo lancamento do tipo Parcela de Cartao SHALL possuir, alem dos campos comuns de
lancamento, o Total de parcelas e o numero da Parcela atual.

#### Scenario: Consulta de progresso de uma parcela
- GIVEN uma compra parcelada em 10x
- WHEN o usuario visualiza a 3a parcela
- THEN o sistema SHALL exibir Total de parcelas = 10 e Parcela atual = 3

### Requirement: Descricao com indicacao de progresso
O sistema SHALL gerar automaticamente a descricao de cada parcela no formato
"<descricao da compra> <parcela atual>/<total de parcelas>".

#### Scenario: Descricao de parcela individual
- GIVEN uma compra de notebook parcelada em 10x
- WHEN o sistema gera o lancamento da segunda parcela
- THEN a Descricao SHALL ser "Compra de notebook 2/10"

### Requirement: Pagamento de fatura e manual e independente
O sistema SHALL tratar o pagamento da fatura do Cartao como um lancamento manual e
independente, registrado pelo usuario. O sistema SHALL NOT gerar automaticamente
uma saida vinculada em nenhuma conta Banco quando uma fatura e paga.

#### Scenario: Usuario paga a fatura do cartao
- GIVEN uma conta Cartao com parcelas previstas no mes
- WHEN o usuario quer refletir a saida do dinheiro de sua conta corrente
- THEN ele SHALL cadastrar manualmente um lancamento de saida na conta Banco
  correspondente, sem nenhuma geracao automatica pelo sistema
