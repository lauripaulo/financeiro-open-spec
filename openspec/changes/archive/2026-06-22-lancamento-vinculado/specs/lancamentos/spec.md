## MODIFIED Requirements

### Requirement: Campos do lancamento
Todo lancamento SHALL possuir: Descricao, Tipo, Data de vencimento, Data de pagamento
(preenchida apenas ao marcar como Pago), Valor, Conta, Lancamento Vinculado (opcional,
referencia ao lancamento par da mesma operacao financeira) e Status (somente leitura,
calculado pelo sistema). O pagamento de um lancamento SHALL ser sempre integral;
pagamento parcial nao e suportado.

#### Scenario: Criacao de um lancamento simples
- GIVEN uma conta ja cadastrada
- WHEN o usuario registra um lancamento com Descricao, Tipo, Data de vencimento,
  Valor e Conta
- THEN o sistema SHALL criar o lancamento com Status calculado automaticamente
- AND Data de pagamento SHALL permanecer vazia ate o lancamento ser marcado como Pago
- AND Lancamento Vinculado SHALL permanecer vazio se nao informado

#### Scenario: Criacao de lancamento com vínculo informado
- GIVEN uma conta ja cadastrada e um lancamento B existente com mesmo valor absoluto
- WHEN o usuario registra um novo lancamento A informando B como lancamento vinculado
- THEN o sistema SHALL criar A com lancamento_vinculado apontando para B
- AND SHALL automaticamente definir B.lancamento_vinculado como A
