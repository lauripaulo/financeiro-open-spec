# Delta Spec: resumo-consolidado (fix-resumo-consolidado-review)

## MODIFIED Requirements

### Requirement: Service unico de consolidacao mensal
O sistema SHALL expor em `visualizacao/services.py` uma funcao `resumo_consolidado(ano, mes, conta_id=None, status=None)` que computa, sem depender de HTTP, request ou sessao: a lista de lancamentos do mes das contas Banco e Cartao (respeitando filtros de conta e status), os totais de entradas e saidas, o saldo total, o saldo inicial de cada conta, os alertas de limite negativo e a conta selecionada resolvida (`conta_selecionada`). O parametro `conta_id` SHALL ser `int` ou `None` — a interpretacao de parametros de request (conversao de string) e responsabilidade exclusiva da view. O resultado SHALL ser um value object imutavel consumido pela view.

#### Scenario: Resumo computado sem cliente HTTP
- **GIVEN** um mes aberto com lancamentos em contas Banco e Cartao
- **WHEN** um teste chama `resumo_consolidado(ano, mes)` diretamente
- **THEN** o resultado SHALL conter lancamentos, totais de entradas/saidas, saldo total, saldos iniciais por conta, alertas de limite e `conta_selecionada`
- **AND** nenhuma interacao HTTP SHALL ser necessaria

#### Scenario: Filtro por conta restringe lista e totais
- **GIVEN** um mes com lancamentos em duas contas
- **WHEN** `resumo_consolidado(ano, mes, conta_id=X)` e chamado com `X` inteiro
- **THEN** a lista de lancamentos e os totais de entradas/saidas SHALL refletir apenas a conta X
- **AND** o saldo total SHALL ser o saldo da conta X
- **AND** `conta_selecionada` SHALL ser a instancia de `Conta` correspondente

#### Scenario: Filtro por status restringe lista, totais e saldos
- **GIVEN** um mes com lancamentos pagos e previstos
- **WHEN** `resumo_consolidado(ano, mes, status=["PAGO"])` e chamado
- **THEN** a lista, os totais e os saldos SHALL considerar apenas lancamentos pagos

#### Scenario: Contas Investimento ficam fora do resumo
- **GIVEN** uma conta do tipo Investimento com lancamentos no mes
- **WHEN** `resumo_consolidado(ano, mes)` e chamado
- **THEN** os lancamentos, totais e saldos SHALL ignorar a conta Investimento

#### Scenario: Alertas de limite cobrem todas as contas Banco mesmo com filtro de conta
- **GIVEN** duas contas Banco, uma delas com saldo alem do limite negativo
- **WHEN** `resumo_consolidado(ano, mes, conta_id=<outra conta>)` e chamado
- **THEN** o alerta de limite da conta ultrapassada SHALL estar presente no resultado

#### Scenario: Parse de parametros de request permanece na view
- **GIVEN** uma requisicao GET com `?conta=<id>` como string
- **WHEN** a view `visao_consolidada` processa a requisicao
- **THEN** a view SHALL converter o parametro para `int` antes de invocar o service
- **AND** o service SHALL NOT realizar conversao de strings de request

### Requirement: Regra de saldo mensal com implementacao unica
O sistema SHALL ter exatamente um corpo de implementacao da regra de saldo mensal de conta (saldo inicial registrado em `SaldoMensalConta`, com fallback em `conta.saldo_atual`, somado a entradas e subtraido de saidas do mes): a funcao batch `saldos_do_mes(contas, ano, mes, status_incluidos=None)` em `meses/services.py`, que retorna saldo inicial e final por conta com numero de consultas independente do numero de contas. `saldo_do_mes(conta, ...)` SHALL ser um wrapper fino sobre `saldos_do_mes`. `resumo_consolidado` SHALL obter os saldos por conta exclusivamente via `saldos_do_mes` — nenhum outro modulo SHALL re-implementar a regra. A funcao `_saldo_final_periodo` SHALL NOT existir; `criar_mes` SHALL usar `saldo_do_mes` para encadear o saldo inicial do mes seguinte.

#### Scenario: Encadeamento de saldo na abertura de mes usa saldo_do_mes
- **GIVEN** um mes aberto com saldo inicial e lancamentos em uma conta
- **WHEN** o mes seguinte e criado via `criar_mes`
- **THEN** o `saldo_inicial` da conta no novo mes SHALL ser igual a `saldo_do_mes(conta, ano_anterior, mes_anterior)`

#### Scenario: Batch concorda com o wrapper escalar
- **GIVEN** duas contas com lancamentos de entradas e saidas no mes
- **WHEN** `saldos_do_mes([conta_a, conta_b], ano, mes)` e chamado
- **THEN** o saldo final de cada conta SHALL ser igual a `saldo_do_mes(conta, ano, mes)` correspondente

#### Scenario: Resumo consolidado concorda com saldo_do_mes para cada conta
- **GIVEN** um mes com lancamentos de entradas e saidas em multiplas contas
- **WHEN** `resumo_consolidado(ano, mes, conta_id=conta.pk)` e computado para CADA conta individualmente, com e sem filtro de status
- **THEN** o `saldo_total` de cada resumo SHALL ser igual a `saldo_do_mes(conta, ano, mes, status_incluidos=status)` da conta correspondente

#### Scenario: Nenhuma copia inline da regra sobrevive
- **WHEN** o codigo de `visualizacao/services.py` e inspecionado
- **THEN** a agregacao de saldo final por conta (fallback + entradas − saidas) SHALL ocorrer somente via chamada a `saldos_do_mes`

### Requirement: Consolidacao em passada unica
O calculo do resumo consolidado SHALL executar um numero constante de consultas, independente do numero de contas e lancamentos, e SHALL NOT recomputar o saldo de uma mesma conta mais de uma vez por invocacao. Os saldos iniciais e finais de todas as contas SHALL sair de uma unica chamada a `saldos_do_mes`.

#### Scenario: Numero de consultas independe do numero de contas
- **GIVEN** cinco contas Banco/Cartao com registros de `SaldoMensalConta` e lancamentos no mes
- **WHEN** `resumo_consolidado(ano, mes)` e executado
- **THEN** o numero de consultas SHALL ser o mesmo que com duas contas
- **AND** SHALL ser pinado por teste (`assertNumQueries`)

#### Scenario: Alertas reutilizam o saldo ja computado
- **GIVEN** contas Banco com limite negativo configurado
- **WHEN** `resumo_consolidado(ano, mes)` computa saldo total e alertas
- **THEN** o saldo de cada conta SHALL ser computado uma unica vez e reutilizado para o total e para os alertas
