# Meses

## Purpose
Definir regras de criacao de meses, propagacao de lancamentos e calculo de saldo.

## Requirements

### Requirement: Criacao manual do mes
O usuario SHALL decidir explicitamente quando criar um novo mes. O sistema SHALL
informar que um mes precisa ser criado antes de poder ser visualizado ou editado.
A abertura de mes SHALL seguir sequencia obrigatoria:
- se nao existir nenhum mes aberto, o primeiro mes permitido SHALL ser o mes/ano
  atual;
- se ja existir ao menos um mes aberto, o unico mes permitido SHALL ser o mes
  imediatamente seguinte ao ultimo mes aberto.
Ao tentar abrir um mes fora da sequencia permitida, o sistema SHALL rejeitar a
operacao e SHALL informar qual mes e permitido naquele momento.

#### Scenario: Tentativa de acessar mes ainda nao criado
- GIVEN o mes de agosto/2026 ainda nao foi criado
- WHEN o usuario tenta visualizar agosto/2026
- THEN o sistema SHALL informar que o mes precisa ser criado primeiro

#### Scenario: Tentativa de criar primeiro mes diferente do mes atual
- GIVEN nao existe nenhum mes aberto no sistema
- WHEN o usuario tenta criar um primeiro mes diferente do mes/ano atual
- THEN o sistema SHALL rejeitar a criacao
- AND SHALL informar o mes permitido

#### Scenario: Tentativa de pular um mes na abertura
- GIVEN o ultimo mes aberto e abril/2026
- WHEN o usuario tenta criar junho/2026
- THEN o sistema SHALL rejeitar a criacao
- AND SHALL informar maio/2026 como mes permitido

#### Scenario: Criacao do mes imediatamente seguinte
- GIVEN o ultimo mes aberto e abril/2026
- WHEN o usuario cria maio/2026
- THEN o sistema SHALL criar o mes normalmente

### Requirement: Limite de meses futuros
O sistema SHALL suportar confortavelmente a criacao de ate 12 meses futuros a
partir do mes atual. Esse limite SHALL ser informativo: o sistema SHALL permitir a
criacao de meses alem desse limite, exibindo um aviso ao usuario.

#### Scenario: Criacao dentro do limite suportado
- GIVEN 11 meses futuros ja criados
- WHEN o usuario cria o 12o mes futuro
- THEN o sistema SHALL criar o mes normalmente, sem aviso

#### Scenario: Criacao alem do limite suportado
- GIVEN 12 meses futuros ja criados
- WHEN o usuario cria um 13o mes futuro
- THEN o sistema SHALL criar o mes normalmente
- AND SHALL exibir um aviso informando que o limite recomendado foi ultrapassado

### Requirement: Primeiro mes do sistema
O primeiro mes criado no sistema SHALL iniciar sem nenhum lancamento, ja que nao ha
mes anterior para servir de base. O primeiro mes do sistema SHALL ser
obrigatoriamente o mes/ano atual. O saldo inicial das contas Banco e Investimento
nesse primeiro mes SHALL ser o valor informado pelo usuario na criacao de cada
conta - o primeiro mes SHALL NOT ser tratado como tendo saldo zero.

#### Scenario: Primeiro mes herda saldo das contas
- GIVEN uma conta Banco criada com saldo atual de R$ 800,00
- WHEN o usuario cria o primeiro mes do sistema no mes atual
- THEN o sistema SHALL exibir R$ 800,00 como saldo inicial dessa conta no mes
- AND o mes SHALL nao conter nenhum lancamento

### Requirement: Novo mes criado a partir do mes anterior
Ao criar um novo mes (a partir do segundo), o sistema SHALL usar o mes anterior
como base para gerar os lancamentos propagaveis, todos iniciando com Status
Previsto.

#### Scenario: Criacao de mes com lancamentos propagados
- GIVEN o mes anterior contem um Gasto Fixo e uma Assinatura
- WHEN o usuario cria o novo mes
- THEN o sistema SHALL gerar copias desses lancamentos no novo mes com Status Previsto

### Requirement: Regras de propagacao por tipo de lancamento
O sistema SHALL aplicar as seguintes regras de propagacao automatica ao criar um
novo mes:
- Gasto Fixo e Recebimento Fixo SHALL ser repetidos no mesmo dia do mes seguinte.
- Assinatura SHALL ser repetida no novo mes.
- Parcela de Cartao SHALL NOT ser propagada na abertura de mes, pois sua geracao e
  responsabilidade do fluxo de compra parcelada.
- Recebimento Excepcional, Gasto Variavel, Conciliacao, Aporte e Resgate SHALL NOT
  ser propagados automaticamente.

#### Scenario: Parcela de cartao nao e propagada ao abrir novo mes
- GIVEN existe uma Parcela de Cartao registrada para um mes ja aberto
- WHEN o usuario cria o mes imediatamente seguinte
- THEN o sistema SHALL NOT gerar nova Parcela de Cartao por propagacao de abertura

### Requirement: Tratamento de lancamentos pendentes do mes anterior
Ao criar um novo mes, o sistema SHALL exibir os lancamentos com Status Pendente do
mes anterior e SHALL solicitar ao usuario que escolha, para cada um, entre mante-lo
no mes anterior ou transferi-lo para o novo mes. O fluxo de abertura do mes SHALL
preservar essas decisoes como parte obrigatoria da conclusao da abertura.

#### Scenario: Usuario transfere um lancamento pendente
- GIVEN um Gasto Fixo com Status Pendente no mes anterior
- WHEN o usuario, ao criar o novo mes, escolhe transferi-lo
- THEN o sistema SHALL mover esse lancamento para o novo mes, mantendo seu Status

#### Scenario: Usuario mantem um lancamento no mes anterior
- GIVEN um lancamento Pendente listado na abertura do novo mes
- WHEN o usuario escolhe manter no mes anterior
- THEN o sistema SHALL manter a competencia original sem mover o lancamento

### Requirement: Validacao de elegibilidade na transferencia de pendente
O sistema SHALL permitir transferencia apenas para lancamentos que sejam pendentes
do mes imediatamente anterior ao mes em abertura. O sistema SHALL bloquear tentativa
de transferencia de lancamentos fora desse criterio.

#### Scenario: Tentativa de transferir lancamento nao elegivel
- WHEN o usuario tenta transferir um lancamento que nao pertence ao mes anterior
  ou nao esta em status Pendente
- THEN o sistema SHALL rejeitar a operacao
- AND SHALL informar que apenas pendentes do mes anterior podem ser transferidos

### Requirement: Edicao de lancamento recorrente afeta meses futuros ja criados
O sistema SHALL aplicar, ao editar um lancamento de um tipo propagavel (Gasto Fixo, Recebimento Fixo ou Assinatura), a alteracao a todas as instancias desse lancamento ja existentes em meses futuros ja criados, e SHALL sobrescrever qualquer customizacao manual feita em uma instancia futura.

#### Scenario: Alteracao de valor do aluguel propaga para meses futuros
- GIVEN um Gasto Fixo "Aluguel" de R$ 1.500,00 ja propagado para os 3 proximos meses
- WHEN o usuario altera o valor para R$ 1.600,00 no mes atual
- THEN o sistema SHALL atualizar o valor para R$ 1.600,00 nos 3 meses futuros ja criados

#### Scenario: Edicao sobrescreve instancia customizada manualmente
- GIVEN um Gasto Fixo "Internet" propagado para os 2 proximos meses
- AND o valor do mes seguinte foi customizado manualmente para R$ 120,00
- WHEN o usuario edita o valor original para R$ 100,00 no mes atual
- THEN o sistema SHALL sobrescrever o valor customizado, deixando R$ 100,00 tambem
  no mes seguinte

### Requirement: Exclusao de lancamento recorrente remove instancias futuras
O sistema SHALL remover, ao excluir um lancamento de um tipo propagavel em um determinado mes, as instancias desse lancamento ja criadas em meses futuros, e SHALL deixar de gera-lo automaticamente nos meses seguintes a partir desse ponto.

#### Scenario: Cancelamento de assinatura remove instancias futuras
- GIVEN uma Assinatura "Streaming X" presente no mes atual e em 2 meses futuros ja criados
- WHEN o usuario exclui esse lancamento no mes atual
- THEN o sistema SHALL remover as instancias ja criadas nos 2 meses futuros
- AND SHALL NOT gerar esse lancamento em novos meses criados depois da exclusao

### Requirement: Saldo inicial do mes herdado do mes anterior
O sistema SHALL usar o saldo final de cada conta no mes anterior como saldo inicial
do mes seguinte. O usuario SHALL poder editar esse saldo inicial; ao faze-lo, o
sistema SHALL registrar automaticamente a diferenca como um lancamento do tipo
Conciliacao.

#### Scenario: Usuario corrige o saldo inicial herdado
- GIVEN o saldo final da conta Banco do Brasil em marco foi R$ 500,00
- WHEN o usuario, em abril, ajusta o saldo inicial para R$ 480,00
- THEN o sistema SHALL registrar um lancamento de Conciliacao de -R$ 20,00 em abril

### Requirement: Calculo do saldo do mes
O sistema SHALL calcular o saldo de uma conta Banco ou Cartao no mes como o saldo
inicial herdado somado a todas as entradas e subtraido de todas as saidas do
periodo, independentemente do Status de cada lancamento (Previsto, Pendente ou
Pago).

#### Scenario: Saldo combina valor herdado e movimentacoes do mes
- GIVEN uma conta com saldo inicial herdado de R$ 100,00 no mes
- WHEN o mes registra R$ 80,00 em entradas e R$ 40,00 em saidas
- THEN o sistema SHALL exibir o saldo do mes como R$ 140,00

### Requirement: Saldo de conta Investimento calculado fora do saldo do mes
O sistema SHALL calcular o saldo acumulado de uma conta Investimento como o saldo
anterior somado aos Aportes e subtraido dos Resgates, mantendo esse total separado
do saldo consolidado mensal de Banco e Cartao.

#### Scenario: Aporte nao altera o saldo do mes de Banco/Cartao
- GIVEN uma conta Investimento e uma conta Banco distintas
- WHEN o usuario registra um Aporte de R$ 200,00 na conta Investimento
- THEN o sistema SHALL NOT alterar o saldo consolidado do mes das contas Banco/Cartao

### Requirement: Filtro de status no calculo do saldo
O usuario SHALL poder filtrar a visualizacao por Status (por exemplo, excluir
lancamentos Pendentes), e o sistema SHALL recalcular o saldo exibido de acordo com
o filtro ativo.

#### Scenario: Saldo recalculado ao excluir lancamentos pendentes
- GIVEN um mes com lancamentos Pago, Pendente e Previsto
- WHEN o usuario aplica um filtro para ocultar lancamentos Pendentes
- THEN o sistema SHALL recalcular o saldo exibido considerando apenas os lancamentos
  
### Requirement: Regra de saldo mensal com implementacao unica
O sistema SHALL ter exatamente um corpo de implementacao da regra de saldo mensal de conta (saldo inicial registrado em `SaldoMensalConta`, com fallback em `conta.saldo_atual`, somado a entradas e subtraido de saidas do mes): a funcao batch `saldos_do_mes(contas, ano, mes, status_incluidos=None)` em `meses/services.py`, que retorna saldo inicial e final por conta com numero de consultas independente do numero de contas. `saldo_do_mes(...)` SHALL ser um wrapper fino sobre `saldos_do_mes`. `resumo_consolidado` SHALL obter os saldos por conta exclusivamente via `saldos_do_mes` — nenhum outro modulo SHALL re-implementar a regra. A funcao `_saldo_final_periodo` SHALL NOT existir; `criar_mes` SHALL usar `saldo_do_mes` para encadear o saldo inicial do mes seguinte.

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

