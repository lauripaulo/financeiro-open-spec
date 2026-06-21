# Delta for Meses

## ADDED Requirements

### Requirement: Criação manual do mês
O usuário SHALL decidir explicitamente quando criar um novo mês. O sistema SHALL
informar que um mês precisa ser criado antes de poder ser visualizado ou editado.

#### Scenario: Tentativa de acessar mês ainda não criado
- GIVEN o mês de agosto/2026 ainda não foi criado
- WHEN o usuário tenta visualizar agosto/2026
- THEN o sistema SHALL informar que o mês precisa ser criado primeiro

### Requirement: Limite de meses futuros
O sistema SHALL suportar confortavelmente a criação de até 12 meses futuros a
partir do mês atual. Esse limite SHALL ser informativo: o sistema SHALL permitir a
criação de meses além desse limite, exibindo um aviso ao usuário.

#### Scenario: Criação dentro do limite suportado
- GIVEN 11 meses futuros já criados
- WHEN o usuário cria o 12º mês futuro
- THEN o sistema SHALL criar o mês normalmente, sem aviso

#### Scenario: Criação além do limite suportado
- GIVEN 12 meses futuros já criados
- WHEN o usuário cria um 13º mês futuro
- THEN o sistema SHALL criar o mês normalmente
- AND SHALL exibir um aviso informando que o limite recomendado foi ultrapassado

### Requirement: Primeiro mês do sistema
O primeiro mês criado no sistema SHALL iniciar sem nenhum lançamento, já que não há
mês anterior para servir de base. O saldo inicial das contas Banco e Investimento
nesse primeiro mês SHALL ser o valor informado pelo usuário na criação de cada
conta — o primeiro mês SHALL NOT ser tratado como tendo saldo zero.

#### Scenario: Primeiro mês herda saldo das contas
- GIVEN uma conta Banco criada com saldo atual de R$ 800,00
- WHEN o usuário cria o primeiro mês do sistema
- THEN o sistema SHALL exibir R$ 800,00 como saldo inicial dessa conta no mês
- AND o mês SHALL não conter nenhum lançamento

### Requirement: Novo mês criado a partir do mês anterior
Ao criar um novo mês (a partir do segundo), o sistema SHALL usar o mês anterior
como base para gerar os lançamentos propagáveis, todos iniciando com Status
Previsto.

#### Scenario: Criação de mês com lançamentos propagados
- GIVEN o mês anterior contém um Gasto Fixo e uma Assinatura
- WHEN o usuário cria o novo mês
- THEN o sistema SHALL gerar cópias desses lançamentos no novo mês com Status Previsto

### Requirement: Regras de propagação por tipo de lançamento
O sistema SHALL aplicar as seguintes regras de propagação automática ao criar um
novo mês:
- Gasto Fixo e Recebimento Fixo SHALL ser repetidos no mesmo dia do mês seguinte.
- Assinatura SHALL ser repetida no novo mês.
- Parcela de Cartão SHALL ser repetida com a Parcela atual acrescida de 1, somente
  enquanto a Parcela atual for menor que o Total de parcelas.
- Recebimento Excepcional, Gasto Variável, Conciliação, Aporte e Resgate SHALL NOT
  ser propagados automaticamente.

#### Scenario: Última parcela não gera nova propagação
- GIVEN uma Parcela de Cartão com Parcela atual = 10 e Total de parcelas = 10
- WHEN um novo mês é criado
- THEN o sistema SHALL NOT gerar uma nova cópia dessa parcela no novo mês

### Requirement: Tratamento de lançamentos pendentes do mês anterior
Ao criar um novo mês, o sistema SHALL exibir os lançamentos com Status Pendente do
mês anterior e SHALL solicitar ao usuário que escolha, para cada um, entre mantê-lo
no mês anterior ou transferi-lo para o novo mês.

#### Scenario: Usuário transfere um lançamento pendente
- GIVEN um Gasto Fixo com Status Pendente no mês anterior
- WHEN o usuário, ao criar o novo mês, escolhe transferi-lo
- THEN o sistema SHALL mover esse lançamento para o novo mês, mantendo seu Status

### Requirement: Edição de lançamento recorrente afeta meses futuros já criados
O sistema SHALL aplicar, ao editar um lançamento de um tipo propagável (Gasto Fixo, Recebimento Fixo ou Assinatura), a alteração a todas as instâncias desse lançamento já existentes em meses futuros já criados, e SHALL sobrescrever qualquer customização manual feita em uma instância futura.

#### Scenario: Alteração de valor do aluguel propaga para meses futuros
- GIVEN um Gasto Fixo "Aluguel" de R$ 1.500,00 já propagado para os 3 próximos meses
- WHEN o usuário altera o valor para R$ 1.600,00 no mês atual
- THEN o sistema SHALL atualizar o valor para R$ 1.600,00 nos 3 meses futuros já criados

#### Scenario: Edição sobrescreve instância customizada manualmente
- GIVEN um Gasto Fixo "Internet" propagado para os 2 próximos meses
- AND o valor do mês seguinte foi customizado manualmente para R$ 120,00
- WHEN o usuário edita o valor original para R$ 100,00 no mês atual
- THEN o sistema SHALL sobrescrever o valor customizado, deixando R$ 100,00 também
  no mês seguinte

### Requirement: Exclusão de lançamento recorrente remove instâncias futuras
O sistema SHALL remover, ao excluir um lançamento de um tipo propagável em um determinado mês, as instâncias desse lançamento já criadas em meses futuros, e SHALL deixar de gerá-lo automaticamente nos meses seguintes a partir desse ponto.

#### Scenario: Cancelamento de assinatura remove instâncias futuras
- GIVEN uma Assinatura "Streaming X" presente no mês atual e em 2 meses futuros já criados
- WHEN o usuário exclui esse lançamento no mês atual
- THEN o sistema SHALL remover as instâncias já criadas nos 2 meses futuros
- AND SHALL NOT gerar esse lançamento em novos meses criados depois da exclusão

### Requirement: Saldo inicial do mês herdado do mês anterior
O sistema SHALL usar o saldo final de cada conta no mês anterior como saldo inicial
do mês seguinte. O usuário SHALL poder editar esse saldo inicial; ao fazê-lo, o
sistema SHALL registrar automaticamente a diferença como um lançamento do tipo
Conciliação.

#### Scenario: Usuário corrige o saldo inicial herdado
- GIVEN o saldo final da conta Banco do Brasil em março foi R$ 500,00
- WHEN o usuário, em abril, ajusta o saldo inicial para R$ 480,00
- THEN o sistema SHALL registrar um lançamento de Conciliação de -R$ 20,00 em abril

### Requirement: Cálculo do saldo do mês
O sistema SHALL calcular o saldo de uma conta Banco ou Cartão no mês como o saldo
inicial herdado somado a todas as entradas e subtraído de todas as saídas do
período, independentemente do Status de cada lançamento (Previsto, Pendente ou
Pago).

#### Scenario: Saldo combina valor herdado e movimentações do mês
- GIVEN uma conta com saldo inicial herdado de R$ 100,00 no mês
- WHEN o mês registra R$ 80,00 em entradas e R$ 40,00 em saídas
- THEN o sistema SHALL exibir o saldo do mês como R$ 140,00

### Requirement: Saldo de conta Investimento calculado fora do saldo do mês
O sistema SHALL calcular o saldo acumulado de uma conta Investimento como o saldo
anterior somado aos Aportes e subtraído dos Resgates, mantendo esse total separado
do saldo consolidado mensal de Banco e Cartão.

#### Scenario: Aporte não altera o saldo do mês de Banco/Cartão
- GIVEN uma conta Investimento e uma conta Banco distintas
- WHEN o usuário registra um Aporte de R$ 200,00 na conta Investimento
- THEN o sistema SHALL NOT alterar o saldo consolidado do mês das contas Banco/Cartão

### Requirement: Filtro de status no cálculo do saldo
O usuário SHALL poder filtrar a visualização por Status (por exemplo, excluir
lançamentos Pendentes), e o sistema SHALL recalcular o saldo exibido de acordo com
o filtro ativo.

#### Scenario: Saldo recalculado ao excluir lançamentos pendentes
- GIVEN um mês com lançamentos Pago, Pendente e Previsto
- WHEN o usuário aplica um filtro para ocultar lançamentos Pendentes
- THEN o sistema SHALL recalcular o saldo exibido considerando apenas os lançamentos
  visíveis após o filtro
