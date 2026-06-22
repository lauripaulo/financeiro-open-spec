# Delta para Meses

## REQUISITOS MODIFICADOS

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
