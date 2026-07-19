## MODIFIED Requirements

### Requirement: Campos do lancamento
Todo lancamento SHALL possuir: Descricao, Tipo, Data de vencimento, Data de pagamento
(preenchida apenas ao marcar como Pago), Valor, Conta, Lancamento Vinculado (opcional,
referencia ao lancamento par da mesma operacao financeira) e Status (somente leitura,
calculado pelo sistema). O vinculo SHALL ser estabelecido exclusivamente pelos fluxos
do sistema (ex.: transferencia entre contas); o formulario de criacao/edicao de
lancamento SHALL NOT expor o campo Lancamento Vinculado para edicao. Na edicao de um
lancamento vinculado, o sistema SHALL exibir a identificacao do par como informacao
somente leitura. O pagamento de um lancamento SHALL ser sempre integral; pagamento
parcial nao e suportado. Quando houver dados invalidos no formulario de lancamento, o
sistema SHALL retornar erros de validacao ao usuario e SHALL NOT levantar erro interno
por ausencia de relacao `conta` durante a validacao.

#### Scenario: Criacao de um lancamento simples
- GIVEN uma conta ja cadastrada
- WHEN o usuario registra um lancamento com Descricao, Tipo, Data de vencimento,
  Valor e Conta
- THEN o sistema SHALL criar o lancamento com Status calculado automaticamente
- AND Data de pagamento SHALL permanecer vazia ate o lancamento ser marcado como Pago
- AND Lancamento Vinculado SHALL permanecer vazio

#### Scenario: Formulario nao expoe vinculo
- GIVEN o formulario de criacao ou edicao de lancamento
- WHEN a pagina e renderizada
- THEN o campo Lancamento Vinculado SHALL NOT estar presente como campo editavel

#### Scenario: Edicao de lancamento vinculado exibe par como somente leitura
- GIVEN um lancamento A vinculado a um lancamento B pelo fluxo de transferencia
- WHEN o usuario abre a edicao de A
- THEN o sistema SHALL exibir a identificacao de B como informacao somente leitura

#### Scenario: Submissao invalida com tipo incompativel nao causa erro interno
- GIVEN uma conta do tipo Banco existente
- WHEN o usuario envia um novo lancamento com tipo APORTE para essa conta
- THEN o sistema SHALL rejeitar a submissao com erro de validacao no formulario
- AND SHALL NOT gerar excecao interna por ausencia de `conta` durante model clean
