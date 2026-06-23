# Visualizacao

## Purpose
Definir as visoes de consulta mensal, historico e acoes de interacao do usuario.

## Requirements

### Requirement: Visao de conta
O sistema SHALL permitir visualizar os lancamentos do mes filtrados por uma unica
conta, exibindo apenas os lancamentos pertencentes a essa conta. Quando essa visao
estiver ativa, os totais exibidos (entradas, saidas e saldo) SHALL refletir apenas
o escopo da conta selecionada.

#### Scenario: Usuario filtra por uma conta especifica
- GIVEN um mes com lancamentos em duas contas diferentes
- WHEN o usuario seleciona a Visao de conta para a conta "Banco do Brasil"
- THEN o sistema SHALL exibir apenas os lancamentos dessa conta

#### Scenario: Totais da visao de conta respeitam a conta selecionada
- GIVEN o usuario esta com filtro de uma conta especifica ativo
- WHEN a tela calcula entradas, saidas e saldo
- THEN o sistema SHALL considerar somente lancamentos da conta selecionada

### Requirement: Identificacao explicita do escopo de saldo na tela principal
O sistema SHALL indicar claramente se o saldo exibido na tela principal representa
o consolidado de Banco+Cartao ou o saldo de uma conta especifica filtrada.

#### Scenario: Tela com conta filtrada informa escopo
- WHEN o usuario aplica filtro por conta na tela principal
- THEN o sistema SHALL exibir rotulo indicando que o saldo mostrado e da conta filtrada

#### Scenario: Tela sem filtro informa consolidado
- WHEN o usuario remove o filtro de conta na tela principal
- THEN o sistema SHALL exibir rotulo indicando que o saldo mostrado e consolidado

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

#### Scenario: Lancamento vinculado exibe conta contraparte na visao consolidada
- GIVEN um lancamento B (GASTO_VARIAVEL) na conta Banco Inter com lancamento_vinculado
  apontando para A (APORTE) na conta Previdencia XP
- WHEN o usuario acessa a Visao consolidada
- THEN a linha de B SHALL exibir na coluna Contraparte o nome "Previdencia XP"
  precedido de indicador de destino (ex.: "→ Previdencia XP")

#### Scenario: Lancamento sem vinculo deixa coluna contraparte vazia
- GIVEN um lancamento sem lancamento_vinculado definido
- WHEN o usuario acessa a Visao consolidada
- THEN a coluna Contraparte dessa linha SHALL permanecer vazia

### Requirement: Ordem das secoes na tela principal
Na tela principal (Visao consolidada), o sistema SHALL apresentar as secoes de
conteudo na seguinte ordem: Cabecalho (navegacao de mes), Avisos, Filtros,
Movimentacoes, Totais, Pendentes do mes anterior e, por ultimo, Ajustar saldo
inicial.

#### Scenario: Usuario acessa a tela principal com um mes ja criado
- **WHEN** o usuario acessa a Visao consolidada de um mes ja criado
- **THEN** o sistema SHALL exibir a secao de Movimentacoes imediatamente apos os
  Filtros
- **AND** SHALL exibir Totais, Pendentes do mes anterior e Ajustar saldo inicial,
  nessa ordem, apos Movimentacoes

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

### Requirement: Navegacao entre meses
O sistema SHALL oferecer um seletor de mes e ano, alem de botoes de navegacao para o
mes anterior e o mes seguinte.

#### Scenario: Navegacao para o mes anterior
- GIVEN o usuario esta visualizando abril/2026
- WHEN ele clica no botao de mes anterior
- THEN o sistema SHALL exibir marco/2026

### Requirement: Feedback explicito para tentativa de abertura de mes fora da sequencia
Quando o usuario tentar abrir um mes fora da sequencia permitida, o sistema SHALL
informar de forma explicita qual e o mes/ano permitido naquele momento e SHALL
orientar a abertura desse mes permitido.

#### Scenario: Usuario tenta abrir mes diferente do permitido
- GIVEN o ultimo mes aberto e abril/2026
- WHEN o usuario tenta abrir junho/2026
- THEN o sistema SHALL informar que maio/2026 e o mes permitido
- AND SHALL exibir acao para abrir o mes permitido

#### Scenario: Usuario tenta criar primeiro mes diferente do atual
- GIVEN nao existe nenhum mes aberto
- WHEN o usuario tenta abrir um primeiro mes diferente do mes atual
- THEN o sistema SHALL informar que somente o mes atual pode ser aberto primeiro

### Requirement: Confirmacao ao editar mes encerrado
O sistema SHALL solicitar confirmacao do usuario antes de permitir a edicao de um
lancamento em um mes ja encerrado (mes passado).

#### Scenario: Usuario tenta editar um lancamento de mes passado
- GIVEN um lancamento em um mes ja encerrado
- WHEN o usuario tenta edita-lo
- THEN o sistema SHALL perguntar "Voce realmente quer editar um mes ja encerrado?"
- AND SHALL so aplicar a edicao apos confirmacao

### Requirement: Comparativo entre meses
O sistema SHALL oferecer uma tela comparativa entre dois meses, com o mes atual e o
mes anterior selecionados por padrao, permitindo ao usuario escolher outros meses
para comparar.

#### Scenario: Comparacao padrao entre mes atual e anterior
- GIVEN o usuario acessa a tela comparativa pela primeira vez
- WHEN a tela carrega
- THEN o sistema SHALL exibir, por padrao, a comparacao entre o mes atual e o mes anterior

### Requirement: Indicacao de status e acoes por lancamento
O sistema SHALL exibir, para cada lancamento na tela principal do mes, seu Status
(Previsto, Pendente ou Pago) e as acoes disponiveis: marcar como Pago, Editar e
Excluir. A acao Excluir SHALL exigir confirmacao explicita do usuario antes de ser
executada.

#### Scenario: Acao de pagar um lancamento Previsto
- GIVEN um lancamento com Status Previsto
- WHEN o usuario aciona a acao "Pagar" e informa a data de pagamento
- THEN o sistema SHALL alterar o Status para Pago

#### Scenario: Exclusao de lancamento exige confirmacao
- GIVEN um lancamento listado na tela principal
- WHEN o usuario aciona "Excluir"
- THEN o sistema SHALL solicitar confirmacao explicita do usuario
- AND SHALL somente excluir o lancamento apos a confirmacao

### Requirement: Atualizacao da tela apos acoes que nao navegam
O sistema SHALL atualizar a pagina atual e exibir uma mensagem de confirmacao ou
erro quando uma acao do usuario (Pagar, Excluir, Transferir pendente, Manter
pendente ou Ajustar saldo) for concluida sem levar o usuario a uma nova URL.

#### Scenario: Tela e atualizada apos excluir um lancamento
- GIVEN um lancamento listado na tela principal
- WHEN o usuario confirma a exclusao desse lancamento
- THEN o sistema SHALL atualizar a tela e remover o lancamento da lista exibida
- AND SHALL exibir uma mensagem confirmando a exclusao

#### Scenario: Tela e atualizada apos marcar um lancamento como pago
- GIVEN um lancamento com Status Previsto ou Pendente
- WHEN o usuario aciona "Pagar" e informa a data de pagamento
- THEN o sistema SHALL atualizar a tela exibindo o lancamento com Status Pago

#### Scenario: Tela e atualizada apos transferir ou manter um pendente
- GIVEN um lancamento Pendente do mes anterior listado na abertura do novo mes
- WHEN o usuario aciona "Transferir" ou "Manter"
- THEN o sistema SHALL atualizar a tela refletindo a decisao tomada
- AND SHALL exibir uma mensagem confirmando o resultado

### Requirement: Acoes primarias exibidas como botoes
O sistema SHALL exibir links que representam uma acao primaria de criacao ou edicao
(por exemplo "Novo lancamento", "Nova compra parcelada" e "Editar") com a mesma
identidade visual dos botoes de formulario da aplicacao, e nao como links de texto
simples.

#### Scenario: Link de acao primaria exibido como botao
- WHEN o usuario acessa a tela principal do mes
- THEN os links "Novo lancamento", "Nova compra parcelada" e "Editar" SHALL ser
  exibidos com aparencia de botao
