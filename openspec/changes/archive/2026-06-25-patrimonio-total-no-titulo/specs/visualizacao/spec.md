## MODIFIED Requirements

### Requirement: Visao de patrimonio (contas Investimento)
O sistema SHALL oferecer uma visao propria para contas do tipo Investimento,
separada da Visao consolidada, mostrando o saldo acumulado de cada conta e o
historico de Aportes e Resgates. Quando um Aporte ou Resgate possuir lancamento
vinculado, o sistema SHALL exibir o nome da conta bancaria de origem ou destino
correspondente.

O titulo da pagina de Visao de patrimonio SHALL exibir o total consolidado de
todas as contas de investimento no formato:
`Visao de patrimonio: Total R$ X.XXX,XX`.

Quando nao houver contas de investimento cadastradas, o titulo SHALL continuar
exibindo o total com valor `R$ 0,00`.

#### Scenario: Usuario consulta o patrimonio acumulado
- GIVEN duas contas Investimento com Aportes e Resgates registrados
- WHEN o usuario acessa a Visao de patrimonio
- THEN o sistema SHALL exibir o saldo acumulado de cada conta Investimento
- AND SHALL exibir o historico de Aportes e Resgates de cada uma

#### Scenario: Titulo exibe total consolidado de patrimonio
- GIVEN duas contas Investimento com saldos acumulados de R$ 100.000,00 e R$ 80.023,23
- WHEN o usuario acessa a Visao de patrimonio
- THEN o titulo da pagina SHALL exibir `Visao de patrimonio: Total R$ 180.023,23`

#### Scenario: Titulo exibe total zerado sem contas de investimento
- GIVEN nao existe nenhuma conta do tipo Investimento cadastrada
- WHEN o usuario acessa a Visao de patrimonio
- THEN o titulo da pagina SHALL exibir `Visao de patrimonio: Total R$ 0,00`

#### Scenario: Aporte vinculado exibe conta bancaria de origem
- GIVEN um lancamento APORTE na conta Previdencia XP com lancamento_vinculado
  apontando para um lancamento na conta Banco Inter
- WHEN o usuario acessa a Visao de patrimonio
- THEN o historico de Aportes de Previdencia XP SHALL exibir "Banco Inter" como
  conta de origem desse aporte

#### Scenario: Resgate vinculado exibe conta bancaria de destino
- GIVEN um lancamento RESGATE na conta Tesouro Direto com lancamento_vinculado
  apontando para um lancamento na conta Nubank
- WHEN o usuario acessa a Visao de patrimonio
- THEN o historico de Resgates de Tesouro Direto SHALL exibir "Nubank" como
  conta de destino desse resgate

#### Scenario: Aporte sem vinculo nao exibe conta bancaria
- GIVEN um lancamento APORTE sem lancamento_vinculado definido
- WHEN o usuario acessa a Visao de patrimonio
- THEN o historico SHALL exibir o aporte sem informacao de conta bancaria de origem
