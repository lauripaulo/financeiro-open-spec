## MODIFIED Requirements

### Requirement: Geracao automatica de lancamentos de parcela
O sistema SHALL criar automaticamente lancamentos do tipo Parcela de Cartao para
uma compra parcelada registrada em conta do tipo Cartao, com vencimentos
ancorados na data da compra e no dia de vencimento configurado na conta Cartao
associada. A geracao SHALL ocorrer no momento do registro da compra parcelada.

Quando o usuario informar `parcelas_pagas`, o sistema SHALL criar apenas as
parcelas restantes da serie original, iniciando em `parcela_atual =
parcelas_pagas + 1` ate `total_parcelas`, preservando:
- numeracao no formato "<descricao da compra> <parcela atual>/<total de parcelas>"
- `total_parcelas` original em cada lancamento gerado
- calculo de valor por parcela com base no `valor_total` e `total_parcelas`
  originais.

Se `parcelas_pagas` for igual a `total_parcelas`, o sistema SHALL rejeitar o
cadastro por nao haver parcelas a gerar.

#### Scenario: Compra parcelada em 10x sem parcelas pagas
- **GIVEN** uma conta do tipo Cartao ja cadastrada com vencimento no dia 10
- **WHEN** o usuario registra uma compra de R$ 100,00 em janeiro, parcelada em 10x, com `parcelas_pagas = 0`
- **THEN** o sistema SHALL criar 10 lancamentos do tipo Parcela de Cartao de R$ 10,00 cada
- **AND** os vencimentos SHALL ir de 10/fevereiro a 10/novembro
- **AND** as descricoes SHALL ir de "Compra ... 1/10" ate "Compra ... 10/10"

#### Scenario: Compra parcelada em 10x com 3 parcelas pagas
- **GIVEN** uma conta do tipo Cartao ja cadastrada com vencimento no dia 10
- **WHEN** o usuario registra uma compra de R$ 100,00 em janeiro, parcelada em 10x, com `parcelas_pagas = 3`
- **THEN** o sistema SHALL criar 7 lancamentos do tipo Parcela de Cartao
- **AND** as descricoes SHALL ir de "Compra ... 4/10" ate "Compra ... 10/10"
- **AND** `parcela_atual` SHALL iniciar em 4 e terminar em 10
- **AND** o vencimento da parcela "4/10" SHALL permanecer ancorado no 4o mes da serie da compra

#### Scenario: Todas as parcelas ja pagas
- **GIVEN** uma compra informada com `total_parcelas = 10`
- **WHEN** o usuario envia o formulario com `parcelas_pagas = 10`
- **THEN** o sistema SHALL rejeitar o cadastro com erro de validacao
- **AND** SHALL NOT criar compra parcelada nem lancamentos de Parcela de Cartao

## ADDED Requirements

### Requirement: Campo parcelas pagas no fluxo de compra parcelada
O formulario de compra parcelada SHALL expor o campo `parcelas_pagas` como
obrigatorio, com valor inicial `0`, e o backend SHALL validar que
`0 <= parcelas_pagas <= total_parcelas`.

#### Scenario: Formulario inicia com parcelas pagas igual a zero
- **WHEN** o usuario abre o formulario de nova compra parcelada
- **THEN** o campo `parcelas_pagas` SHALL iniciar com valor `0`

#### Scenario: Valor acima do total e ajustado no frontend
- **GIVEN** o usuario informou `parcelas_pagas = 8` e `total_parcelas = 10`
- **WHEN** ele altera `total_parcelas` para `6`
- **THEN** a interface SHALL ajustar automaticamente `parcelas_pagas` para `6`
- **AND** o limite maximo digitavel de `parcelas_pagas` SHALL ser `6`

#### Scenario: Backend rejeita parcelas pagas fora da faixa
- **WHEN** o usuario envia o formulario com `parcelas_pagas = -1` ou `parcelas_pagas > total_parcelas`
- **THEN** o sistema SHALL rejeitar a submissao com erro de validacao
