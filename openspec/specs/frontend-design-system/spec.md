# Frontend Design System

## Purpose
Definir o sistema de design das paginas de usuario (Material Design 3), incluindo
consistencia visual, escopo de aplicacao, acessibilidade minima e responsividade.

## Requirements

### Requirement: Adocao do Material Design 3 nas paginas de usuario
O sistema SHALL aplicar o sistema de design Material Design 3 (M3) do Google -
tokens de cor, escala tipografica, forma, elevacao e camadas de estado - de forma
consistente em todas as paginas renderizadas para o usuario final (apps `contas`,
`lancamentos` e `visualizacao`), sem introduzir framework JS ou pipeline de build.

#### Scenario: Pagina de usuario usa tokens de cor M3
- GIVEN uma pagina de qualquer app de usuario (`contas`, `lancamentos`,
  `visualizacao`)
- WHEN a pagina e renderizada
- THEN os elementos visuais (botoes, cartoes, tabelas, campos, avisos) SHALL usar as
  variaveis de cor definidas nos tokens M3, e nao cores fixas definidas
  individualmente por template

#### Scenario: Componentes reutilizaveis compartilham a mesma folha de estilo
- GIVEN duas paginas distintas que exibem botoes, campos ou cartoes
- WHEN essas paginas sao comparadas visualmente
- THEN ambas SHALL usar as mesmas classes de componente M3, garantindo aparencia
  consistente entre paginas

### Requirement: Painel administrativo do Django permanece inalterado
O sistema SHALL manter o painel administrativo padrao do Django (`/admin/`) sem
qualquer alteracao de estilo decorrente da adocao do Material Design 3.

#### Scenario: Admin nao recebe estilos M3
- GIVEN o usuario acessa `/admin/`
- WHEN a pagina e carregada
- THEN o sistema SHALL exibir o admin com a aparencia padrao do Django, sem os
  estilos, fontes ou icones M3 aplicados as paginas de usuario

### Requirement: Acessibilidade minima dos componentes M3
O sistema SHALL garantir, para todo elemento interativo (botoes, links de acao,
campos de formulario, checkboxes) nas paginas migradas, uma area de toque minima de
48x48dp, contraste de texto adequado (AA) entre cor de texto e cor de fundo definida
pelos tokens M3, e um indicador visual de foco perceptivel ao navegar via teclado.
Todo botao ou link de acao que exiba apenas um icone, sem texto visivel, SHALL
possuir rotulo acessivel (`aria-label`) descrevendo a acao. Botoes somente-icone
SHALL ser usados apenas para acoes CRUD padronizadas (ex.: Editar, Excluir, Pagar)
em celulas de acao de tabelas ou listas; acoes de decisao de fluxo ou destrutivas
com mais de uma opcao SHALL manter rotulo textual visivel.

#### Scenario: Botao de acao tem area de toque adequada
- GIVEN um botao de acao (ex.: "Editar", "Excluir") em qualquer tabela de listagem
- WHEN o elemento e inspecionado
- THEN sua area de toque efetiva SHALL ser de no minimo 48x48dp, mesmo que o
  elemento visual seja menor

#### Scenario: Botao somente-icone possui rotulo acessivel
- GIVEN um botao ou link de acao que exibe apenas um icone, sem texto visivel
- WHEN o elemento e inspecionado
- THEN o elemento SHALL possuir `aria-label` descrevendo a acao
- AND SHALL possuir `title` com o mesmo texto para dica visual ao passar o mouse

#### Scenario: Decisao de fluxo mantem rotulo textual
- GIVEN uma acao de decisao de fluxo (ex.: Transferir/Manter pendente) ou uma
  escolha destrutiva com mais de uma opcao (ex.: excluir lancamento com par vinculado)
- WHEN a acao e exibida ao usuario
- THEN o botao SHALL exibir rotulo textual visivel, nao apenas icone

#### Scenario: Navegacao por teclado exibe foco visivel
- GIVEN o usuario navega pela pagina usando apenas o teclado (Tab)
- WHEN o foco passa por um botao, link ou campo de formulario
- THEN o sistema SHALL exibir um indicador visual de foco claramente perceptivel

### Requirement: Tabelas responsivas em telas estreitas
O sistema SHALL permitir a rolagem horizontal de tabelas de dados quando a largura
da tela for menor que a largura da tabela, sem quebrar o layout da pagina.

#### Scenario: Tabela larga em tela estreita permite rolagem horizontal
- GIVEN uma tabela de dados mais larga que a viewport (ex.: tela de 360px)
- WHEN o usuario acessa a pagina em um dispositivo com essa largura
- THEN o sistema SHALL permitir rolagem horizontal apenas da tabela, mantendo o
  restante do layout da pagina estavel

### Requirement: Confirmacao de exclusao mantem semantica apos migracao visual
O sistema SHALL manter, apos a migracao visual para M3, a exigencia de confirmacao
explicita do usuario antes de excluir um lancamento vinculado (par), exibindo essa
confirmacao com a nova identidade visual M3 (banner de confirmacao) sem alterar o
fluxo de confirmacao existente.

#### Scenario: Confirmacao de exclusao de par exibida com estilo M3
- GIVEN um lancamento com par vinculado listado na tela principal
- WHEN o usuario aciona "Excluir" para esse lancamento
- THEN o sistema SHALL exibir a confirmacao em um banner com identidade visual M3
- AND SHALL somente excluir o lancamento apos a confirmacao explicita, como ja
  ocorria antes da migracao visual

### Requirement: Largura de conteudo contida
O sistema SHALL limitar a largura do conteudo das paginas de usuario: o container
global SHALL ter largura maxima de 1200px centrado na viewport, e as paginas de
criacao/edicao (formularios) SHALL envolver o formulario em um wrapper com largura
maxima de 600px centrado.

#### Scenario: Pagina de listagem em tela larga
- GIVEN uma viewport com largura superior a 1200px
- WHEN qualquer pagina de usuario e renderizada
- THEN o conteudo SHALL ocupar no maximo 1200px, centrado horizontalmente

#### Scenario: Formulario em tela larga
- GIVEN uma viewport com largura superior a 1200px
- WHEN uma pagina de criacao ou edicao e renderizada
- THEN o formulario SHALL ocupar no maximo 600px, centrado no container

### Requirement: Layout de formulario em grid de duas colunas
Os formularios de criacao/edicao SHALL organizar os campos em um grid de duas
colunas, onde campos de texto livre (descricao) e selects ocupam a linha inteira e
campos curtos (datas, numeros, valores monetarios) ocupam meia coluna.

#### Scenario: Campos curtos lado a lado
- GIVEN o formulario de lancamento
- WHEN a pagina e renderizada em desktop
- THEN `data_vencimento` e `valor` SHALL aparecer lado a lado na mesma linha

#### Scenario: Campos longos em linha cheia
- GIVEN qualquer formulario de criacao/edicao
- WHEN a pagina e renderizada
- THEN o campo de descricao e os selects SHALL ocupar a largura total do grid

### Requirement: Campos condicionais por selecao
Os formularios cujos campos so sao validos para determinadas selecoes SHALL
esconder os campos irrelevantes para a selecao atual e desabilita-los (para que nao
sejam submetidos), reexibindo-os e reabilitando-os quando a selecao os tornar
relevantes. A validacao server-side existente permanece a fonte de verdade. No
formulario de conta: tipo Cartao mostra apenas `dia_vencimento`; tipo Banco mostra
`saldo_atual` e `limite_negativo`; tipo Investimento mostra apenas `saldo_atual`.
No formulario de lancamento, a selecao do tipo SHALL filtrar as contas exibidas:
APORTE/RESGATE mostram apenas contas Investimento; os demais tipos escondem contas
Investimento.

#### Scenario: Conta Cartao esconde campos de banco
- GIVEN o formulario de conta com tipo CARTAO selecionado
- WHEN o usuario visualiza o formulario
- THEN `saldo_atual` e `limite_negativo` SHALL estar ocultos e desabilitados
- AND `dia_vencimento` SHALL estar visivel

#### Scenario: Troca de tipo preserva valor ate salvar
- GIVEN edicao de conta Banco com `saldo_atual` preenchido
- WHEN o usuario troca o tipo para CARTAO e depois volta para BANCO sem salvar
- THEN `saldo_atual` SHALL reaparecer com o valor original preservado

#### Scenario: Campo oculto nao gera erro de validacao invisivel
- GIVEN edicao de conta Banco com `saldo_atual` preenchido
- WHEN o usuario troca o tipo para CARTAO e submete
- THEN o campo oculto desabilitado SHALL NOT ser submetido
- AND a submissao SHALL ser aceita sem erro de validacao em campo invisivel

#### Scenario: Tipo APORTE filtra contas para Investimento
- GIVEN o formulario de lancamento com uma conta Banco selecionada
- WHEN o usuario seleciona o tipo APORTE
- THEN o select de conta SHALL exibir apenas contas Investimento
- AND a selecao incompativel anterior SHALL ser limpa

### Requirement: Organizacao da visao consolidada
A visao consolidada SHALL exibir os totais do mes (Entradas, Saidas, Saldo) como
cartoes de destaque no topo da pagina, logo abaixo do cabecalho; SHALL agrupar a
navegacao de mes e os filtros em uma unica barra compacta; e SHALL apresentar as
secoes "Pendentes do mes anterior" e "Ajustar saldo inicial" como blocos
colapsaveis fechados por padrao, sendo que o titulo de pendentes SHALL exibir a
contagem de itens com um badge de destaque quando houver ao menos um item. A tabela
de movimentacoes SHALL manter sua estrutura de colunas e legibilidade.

#### Scenario: Totais visiveis sem rolagem
- GIVEN a visao consolidada de um mes com lancamentos
- WHEN a pagina e carregada em desktop
- THEN Entradas, Saidas e Saldo SHALL estar visiveis no topo, antes da tabela

#### Scenario: Pendencias sinalizadas mesmo colapsadas
- GIVEN 3 lancamentos pendentes do mes anterior
- WHEN a visao consolidada e carregada
- THEN a secao de pendentes SHALL estar fechada
- AND seu titulo SHALL exibir a contagem 3 com badge de destaque

#### Scenario: Secoes colapsaveis sem pendencias
- GIVEN nenhum lancamento pendente do mes anterior
- WHEN a visao consolidada e carregada
- THEN o titulo da secao de pendentes SHALL aparecer sem badge de destaque

### Requirement: Acao de pagar em popover
A acao de marcar um lancamento como pago na tabela de movimentacoes SHALL ser
acionada por um botao compacto que abre um popover contendo o campo de data
pre-preenchido com a data atual e um botao de confirmacao. A confirmacao SHALL
executar a mesma operacao de pagamento existente.

#### Scenario: Pagar com data de hoje
- GIVEN um lancamento pendente na tabela de movimentacoes
- WHEN o usuario clica no botao de pagar e confirma no popover
- THEN o lancamento SHALL ser marcado como pago com a data atual

#### Scenario: Pagar com data retroativa
- GIVEN um lancamento pendente
- WHEN o usuario abre o popover, altera a data e confirma
- THEN o lancamento SHALL ser marcado como pago com a data informada
