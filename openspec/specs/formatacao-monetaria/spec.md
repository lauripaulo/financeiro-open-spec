# Formatacao Monetaria

## Purpose
Definir o padrao de exibicao e de mascara de entrada para todo valor monetario do sistema, no formato brasileiro (R$, separador de milhar ".", separador decimal ",", 2 casas decimais).

## Requirements

### Requirement: Exibicao de valores monetarios no padrao brasileiro
Todo valor monetario exibido em tela (saldo de conta, limite negativo, valor de lancamento, totais de entrada/saida/saldo, valor de movimentacao de patrimonio) SHALL ser formatado no padrao `R$ 1.234,56`: prefixo "R$", separador de milhar ".", separador decimal ",", sempre com exatamente 2 casas decimais.

#### Scenario: Valor com milhar exibido na lista de contas
- GIVEN uma conta tem saldo atual de 256432.11
- WHEN a lista de contas e exibida
- THEN o sistema SHALL exibir "R$ 256.432,11"

#### Scenario: Valor sem casas decimais informadas
- GIVEN um valor monetario e armazenado como 100 (sem casas decimais explicitas)
- WHEN o valor e exibido
- THEN o sistema SHALL exibir "R$ 100,00"

#### Scenario: Saldo de conta nao informado
- GIVEN uma conta nao possui saldo atual informado (campo vazio)
- WHEN o saldo e exibido
- THEN o sistema SHALL exibir "R$ 0,00" no lugar de um valor em branco

#### Scenario: Valor monetario negativo
- GIVEN um lancamento de conciliacao possui valor negativo, por exemplo -1234.56
- WHEN o valor e exibido
- THEN o sistema SHALL exibir "-R$ 1.234,56"

### Requirement: Mascara de digitacao nos campos de entrada monetarios
Todo campo de entrada de valor monetario (saldo atual, limite negativo, valor de lancamento, valor de compra parcelada) SHALL aplicar, durante a digitacao, uma mascara que formata o numero no padrao brasileiro (separador de milhar ".", separador decimal ","), exibindo o prefixo "R$" como elemento visual fixo ao lado do campo, fora do valor editavel.

#### Scenario: Usuario digita um valor em um campo monetario
- GIVEN o usuario esta preenchendo o campo de valor de um lancamento
- WHEN ele digita os numeros correspondentes a 1234.56
- THEN o campo SHALL exibir "1.234,56" formatado em tempo real
- AND o prefixo "R$" SHALL ser exibido ao lado do campo, sem fazer parte do valor digitavel

#### Scenario: Envio do formulario preserva o valor numerico esperado pelo backend
- GIVEN o usuario digitou "1.234,56" em um campo de valor monetario mascarado
- WHEN o formulario e submetido
- THEN o valor enviado ao servidor SHALL ser o decimal simples equivalente (1234.56), sem separador de milhar e com "." como separador decimal

#### Scenario: Formulario reexibido apos erro de validacao mantem o valor digitado
- GIVEN o usuario submeteu um formulario com um campo monetario preenchido e algum outro campo invalido
- WHEN o formulario e reexibido com a mensagem de erro
- THEN o campo monetario SHALL continuar exibindo o valor digitado pelo usuario, formatado no padrao brasileiro
