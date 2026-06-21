# Meses

## Purpose
Definir regras de criacao de meses, propagacao de lancamentos e calculo de saldo.

## Requirements

### Requirement: Criacao manual do mes
O usuario SHALL decidir explicitamente quando criar um novo mes. O sistema SHALL
informar que um mes precisa ser criado antes de poder ser visualizado ou editado.

#### Scenario: Tentativa de acessar mes ainda nao criado
- GIVEN o mes de agosto/2026 ainda nao foi criado
- WHEN o usuario tenta visualizar agosto/2026
- THEN o sistema SHALL informar que o mes precisa ser criado primeiro

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
mes anterior para servir de base. O saldo inicial das contas Banco e Investimento
nesse primeiro mes SHALL ser o valor informado pelo usuario na criacao de cada
conta - o primeiro mes SHALL NOT ser tratado como tendo saldo zero.

#### Scenario: Primeiro mes herda saldo das contas
- GIVEN uma conta Banco criada com saldo atual de R$ 800,00
- WHEN o usuario cria o primeiro mes do sistema
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
- Parcela de Cartao SHALL ser repetida com a Parcela atual acrescida de 1, somente
  enquanto a Parcela atual for menor que o Total de parcelas.
- Recebimento Excepcional, Gasto Variavel, Conciliacao, Aporte e Resgate SHALL NOT
  ser propagados automaticamente.

#### Scenario: Ultima parcela nao gera nova propagacao
- GIVEN uma Parcela de Cartao com Parcela atual = 10 e Total de parcelas = 10
- WHEN um novo mes e criado
- THEN o sistema SHALL NOT gerar uma nova copia dessa parcela no novo mes

### Requirement: Tratamento de lancamentos pendentes do mes anterior
Ao criar um novo mes, o sistema SHALL exibir os lancamentos com Status Pendente do
mes anterior e SHALL solicitar ao usuario que escolha, para cada um, entre mante-lo
no mes anterior ou transferi-lo para o novo mes.

#### Scenario: Usuario transfere um lancamento pendente
- GIVEN um Gasto Fixo com Status Pendente no mes anterior
- WHEN o usuario, ao criar o novo mes, escolhe transferi-lo
- THEN o sistema SHALL mover esse lancamento para o novo mes, mantendo seu Status

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
  visiveis apos o filtro
