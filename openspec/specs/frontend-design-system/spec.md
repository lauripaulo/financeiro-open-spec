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
