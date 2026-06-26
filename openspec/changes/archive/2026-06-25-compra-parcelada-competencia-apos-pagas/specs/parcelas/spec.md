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

Para geracao parcial com `parcelas_pagas > 0`, a primeira parcela restante
SHALL ter `competencia_ano/mes` e `data_vencimento` no mes imediatamente
seguinte ao da compra, e as demais SHALL seguir sequencialmente mes a mes,
sem saltar meses por causa da numeracao original.

Se `parcelas_pagas` for igual a `total_parcelas`, o sistema SHALL rejeitar o
cadastro por nao haver parcelas a gerar.

#### Scenario: Compra parcelada em 10x sem parcelas pagas
- **GIVEN** uma conta do tipo Cartao ja cadastrada com vencimento no dia 10
- **WHEN** o usuario registra uma compra de R$ 100,00 em janeiro, parcelada em 10x, com `parcelas_pagas = 0`
- **THEN** o sistema SHALL criar 10 lancamentos do tipo Parcela de Cartao de R$ 10,00 cada
- **AND** os vencimentos SHALL ir de 10/fevereiro a 10/novembro
- **AND** as descricoes SHALL ir de "Compra ... 1/10" ate "Compra ... 10/10"

#### Scenario: Compra parcelada em 10x com 5 parcelas pagas
- **GIVEN** uma conta do tipo Cartao com vencimento no dia 10
- **AND** uma compra em `25/06/2026` com `total_parcelas = 10` e `parcelas_pagas = 5`
- **WHEN** o sistema gera as parcelas restantes
- **THEN** a primeira parcela gerada SHALL ser `6/10` com `competencia_mes = 7` e `competencia_ano = 2026`
- **AND** a primeira parcela gerada SHALL ter `data_vencimento` em julho de 2026
- **AND** as parcelas seguintes SHALL ter competencias agosto, setembro, outubro e novembro de 2026

#### Scenario: Todas as parcelas ja pagas
- **GIVEN** uma compra informada com `total_parcelas = 10`
- **WHEN** o usuario envia o formulario com `parcelas_pagas = 10`
- **THEN** o sistema SHALL rejeitar o cadastro com erro de validacao
- **AND** SHALL NOT criar compra parcelada nem lancamentos de Parcela de Cartao
