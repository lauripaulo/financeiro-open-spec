# Delta Spec: resumo-consolidado

## ADDED Requirements

### Requirement: Service unico de consolidacao mensal
O sistema SHALL expor em `visualizacao/services.py` uma funcao `resumo_consolidado(ano, mes, conta_id=None, status=None)` que computa, sem depender de HTTP, request ou sessao: a lista de lancamentos do mes das contas Banco e Cartao (respeitando filtros de conta e status), os totais de entradas e saidas, o saldo total, o saldo inicial de cada conta e os alertas de limite negativo. O resultado SHALL ser um value object imutavel consumido pela view.

#### Scenario: Resumo computado sem cliente HTTP
- **GIVEN** um mes aberto com lancamentos em contas Banco e Cartao
- **WHEN** um teste chama `resumo_consolidado(ano, mes)` diretamente
- **THEN** o resultado SHALL conter lancamentos, totais de entradas/saidas, saldo total, saldos iniciais por conta e alertas de limite
- **AND** nenhuma interacao HTTP SHALL ser necessaria

#### Scenario: Filtro por conta restringe lista e totais
- **GIVEN** um mes com lancamentos em duas contas
- **WHEN** `resumo_consolidado(ano, mes, conta_id=X)` e chamado
- **THEN** a lista de lancamentos e os totais de entradas/saidas SHALL refletir apenas a conta X
- **AND** o saldo total SHALL ser o saldo da conta X

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

### Requirement: Regra de saldo mensal com implementacao unica
O sistema SHALL ter exatamente uma implementacao da regra de saldo mensal de conta (saldo inicial registrado em `SaldoMensalConta`, com fallback em `conta.saldo_atual`, somado a entradas e subtraido de saidas do mes): a funcao `saldo_do_mes` em `meses/services.py`. A funcao `_saldo_final_periodo` SHALL NOT existir; `criar_mes` SHALL usar `saldo_do_mes` para encadear o saldo inicial do mes seguinte. Os saldos por conta computados por `resumo_consolidado` SHALL concordar com `saldo_do_mes` para as mesmas entradas.

#### Scenario: Encadeamento de saldo na abertura de mes usa saldo_do_mes
- **GIVEN** um mes aberto com saldo inicial e lancamentos em uma conta
- **WHEN** o mes seguinte e criado via `criar_mes`
- **THEN** o `saldo_inicial` da conta no novo mes SHALL ser igual a `saldo_do_mes(conta, ano_anterior, mes_anterior)`

#### Scenario: Resumo consolidado concorda com saldo_do_mes
- **GIVEN** um mes com lancamentos de entradas e saidas em multiplas contas, com e sem filtro de status
- **WHEN** `resumo_consolidado` computa o saldo de cada conta
- **THEN** cada saldo SHALL ser igual ao retorno de `saldo_do_mes(conta, ano, mes, status_incluidos=status)`

### Requirement: Consolidacao em passada unica
O calculo do resumo consolidado SHALL buscar os saldos iniciais de todas as contas do mes em uma unica consulta e SHALL computar totais, saldos por conta e alertas sem recomputar o saldo de uma mesma conta mais de uma vez por requisicao.

#### Scenario: Saldos iniciais buscados em consulta unica
- **GIVEN** cinco contas Banco/Cartao com registros de `SaldoMensalConta` no mes
- **WHEN** `resumo_consolidado(ano, mes)` e executado
- **THEN** os saldos iniciais SHALL ser obtidos em uma unica consulta a `SaldoMensalConta`, nao uma por conta

#### Scenario: Alertas reutilizam o saldo ja computado
- **GIVEN** contas Banco com limite negativo configurado
- **WHEN** `resumo_consolidado(ano, mes)` computa saldo total e alertas
- **THEN** o saldo de cada conta SHALL ser computado uma unica vez e reutilizado para o total e para os alertas

### Requirement: View consolidada como camada fina
A view `visao_consolidada` SHALL limitar-se a: interpretar parametros da requisicao, aplicar o gate de mes nao criado, invocar `resumo_consolidado`, resolver navegacao de mes e estado de sessao, e renderizar o template. A view SHALL NOT conter loops de agregacao de valores, consultas a `SaldoMensalConta` nem regras de limite negativo. O comportamento observavel da tela SHALL permanecer identico ao anterior.

#### Scenario: Tela consolidada preserva comportamento
- **GIVEN** um mes aberto com lancamentos, filtros de conta e status aplicados
- **WHEN** o usuario acessa a Visao consolidada
- **THEN** os lancamentos exibidos, totais, saldos e alertas SHALL ser identicos aos produzidos pela implementacao anterior

#### Scenario: Logica de dominio ausente da view
- **WHEN** a view `visao_consolidada` e inspecionada
- **THEN** agregacoes de entradas/saidas, fallback de saldo inicial e regras de limite SHALL residir em `visualizacao/services.py`, nao na view
