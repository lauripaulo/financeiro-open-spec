## MODIFIED Requirements

### Requirement: Visao consolidada
O sistema SHALL permitir visualizar todos os lancamentos do mes das contas Banco e
Cartao, ordenados por data de vencimento, com uma coluna indicando a qual conta
cada lancamento pertence e uma coluna "Contraparte" exibindo o nome da conta do
lancamento vinculado quando presente. Contas do tipo Investimento SHALL NOT aparecer
na Visao consolidada.

#### Scenario: Usuario consulta a visao consolidada do mes
- GIVEN um mes com lancamentos em uma conta Banco e uma conta Cartao
- WHEN o usuario acessa a Visao consolidada
- THEN o sistema SHALL listar todos os lancamentos dessas contas em ordem de data
  de vencimento
- AND cada linha SHALL indicar a conta correspondente

#### Scenario: Lançamento vinculado exibe conta contraparte na visão consolidada
- GIVEN um lancamento B (GASTO_VARIAVEL) na conta Banco Inter com lancamento_vinculado
  apontando para A (APORTE) na conta Previdencia XP
- WHEN o usuario acessa a Visao consolidada
- THEN a linha de B SHALL exibir na coluna Contraparte o nome "Previdencia XP"
  precedido de indicador de destino (ex.: "→ Previdencia XP")

#### Scenario: Lançamento sem vínculo deixa coluna contraparte vazia
- GIVEN um lancamento sem lancamento_vinculado definido
- WHEN o usuario acessa a Visao consolidada
- THEN a coluna Contraparte dessa linha SHALL permanecer vazia

### Requirement: Visao de patrimonio (contas Investimento)
O sistema SHALL oferecer uma visao propria para contas do tipo Investimento,
separada da Visao consolidada, mostrando o saldo acumulado de cada conta e o
historico de Aportes e Resgates. Quando um Aporte ou Resgate possuir lancamento
vinculado, o sistema SHALL exibir o nome da conta bancaria de origem ou destino
correspondente.

#### Scenario: Usuario consulta o patrimonio acumulado
- GIVEN duas contas Investimento com Aportes e Resgates registrados
- WHEN o usuario acessa a Visao de patrimonio
- THEN o sistema SHALL exibir o saldo acumulado de cada conta Investimento
- AND SHALL exibir o historico de Aportes e Resgates de cada uma

#### Scenario: Aporte vinculado exibe conta bancária de origem
- GIVEN um lancamento APORTE na conta Previdencia XP com lancamento_vinculado
  apontando para um lancamento na conta Banco Inter
- WHEN o usuario acessa a Visao de patrimonio
- THEN o historico de Aportes de Previdencia XP SHALL exibir "Banco Inter" como
  conta de origem desse aporte

#### Scenario: Resgate vinculado exibe conta bancária de destino
- GIVEN um lancamento RESGATE na conta Tesouro Direto com lancamento_vinculado
  apontando para um lancamento na conta Nubank
- WHEN o usuario acessa a Visao de patrimonio
- THEN o historico de Resgates de Tesouro Direto SHALL exibir "Nubank" como
  conta de destino desse resgate

#### Scenario: Aporte sem vínculo não exibe conta bancária
- GIVEN um lancamento APORTE sem lancamento_vinculado definido
- WHEN o usuario acessa a Visao de patrimonio
- THEN o historico SHALL exibir o aporte sem informacao de conta bancaria de origem
