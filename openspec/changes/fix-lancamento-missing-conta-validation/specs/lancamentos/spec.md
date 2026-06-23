## MODIFIED Requirements

### Requirement: Campos do lancamento
Todo lancamento SHALL possuir: Descricao, Tipo, Data de vencimento, Data de pagamento
(preenchida apenas ao marcar como Pago), Valor, Conta, Lancamento Vinculado (opcional,
referencia ao lancamento par da mesma operacao financeira) e Status (somente leitura,
calculado pelo sistema). O pagamento de um lancamento SHALL ser sempre integral;
pagamento parcial nao e suportado. Quando houver dados invalidos no formulario de
lancamento, o sistema SHALL retornar erros de validacao ao usuario e SHALL NOT
levantar erro interno por ausencia de relacao `conta` durante a validacao.

#### Scenario: Criacao de um lancamento simples
- GIVEN uma conta ja cadastrada
- WHEN o usuario registra um lancamento com Descricao, Tipo, Data de vencimento,
  Valor e Conta
- THEN o sistema SHALL criar o lancamento com Status calculado automaticamente
- AND Data de pagamento SHALL permanecer vazia ate o lancamento ser marcado como Pago
- AND Lancamento Vinculado SHALL permanecer vazio se nao informado

#### Scenario: Criacao de lancamento com vinculo informado
- GIVEN uma conta ja cadastrada e um lancamento B existente com mesmo valor absoluto
- WHEN o usuario registra um novo lancamento A informando B como lancamento vinculado
- THEN o sistema SHALL criar A com lancamento_vinculado apontando para B
- AND SHALL automaticamente definir B.lancamento_vinculado como A

#### Scenario: Submissao invalida com tipo incompativel nao causa erro interno
- GIVEN uma conta do tipo Banco existente
- WHEN o usuario envia um novo lancamento com tipo APORTE para essa conta
- THEN o sistema SHALL rejeitar a submissao com erro de validacao no formulario
- AND SHALL NOT gerar excecao interna por ausencia de `conta` durante model clean
