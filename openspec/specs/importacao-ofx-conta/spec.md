# Importacao OFX Conta

## Purpose
Definir regras para importacao de extrato OFX da conta corrente Nubank:
mapeamento de tipos, item nascendo pago, pulo do pagamento de fatura,
deduplicacao por FITID e exigencia de mes aberto.

## Requirements

### Requirement: Opcao de importacao de extrato da conta Nubank
A pagina Importar SHALL oferecer a opcao "OFX da conta Nubank" com formulario contendo arquivo OFX, conta de destino restrita ao tipo Banco e modo de importacao (somente itens novos ou sobrescrever existentes).

#### Scenario: Card visivel no indice
- **WHEN** o usuario acessa a pagina Importar
- **THEN** ve a opcao de importar OFX da conta Nubank alem da opcao do cartao

#### Scenario: Conta de cartao nao selecionavel
- **WHEN** o usuario abre o formulario de importacao da conta
- **THEN** o seletor de conta lista apenas contas do tipo Banco

### Requirement: Mapeamento de transacoes do extrato
Cada transacao DEBIT do extrato SHALL virar lancamento Gasto Variavel e cada CREDIT SHALL virar Recebimento Excepcional, ambos com valor absoluto, descricao igual ao memo, competencia do mes de DTPOSTED e marcados como gerados automaticamente.

#### Scenario: Compra no debito importada
- **WHEN** o extrato contem DEBIT de -80.72 com memo "Compra no debito - NG MAN YAM" em 01/07/2026
- **THEN** e criado Gasto Variavel de 80.72 na competencia 07/2026 com essa descricao

#### Scenario: Pix recebido importado
- **WHEN** o extrato contem CREDIT de 432.00 com memo de transferencia recebida
- **THEN** e criado Recebimento Excepcional de 432.00

#### Scenario: Memo com padrao de parcela nao gera compra parcelada
- **WHEN** uma transacao da conta tem memo terminando em "- Parcela 2/3"
- **THEN** ela e importada como item simples, sem criar Compra Parcelada nem Parcela de Cartao

### Requirement: Lancamento de extrato nasce pago
Lancamento importado do extrato da conta SHALL nascer com data de pagamento e data de vencimento iguais a data da transacao (DTPOSTED), resultando em status Pago.

#### Scenario: Status pago apos importacao
- **WHEN** uma transacao de 01/07/2026 e importada
- **THEN** o lancamento tem data_pagamento = data_vencimento = 01/07/2026 e status Pago

### Requirement: Pagamento de fatura pulado
Transacao DEBIT com memo "Pagamento de fatura" SHALL ser pulada, pois e a contraparte do "Pagamento recebido" ja pulado na importacao do cartao; importa-la duplicaria os gastos do cartao.

#### Scenario: Pagamento de fatura ignorado
- **WHEN** o extrato contem DEBIT com memo "Pagamento de fatura"
- **THEN** nenhum lancamento e criado e o item aparece como pulado no resultado com motivo

#### Scenario: Credito com mesmo memo nao e pulado
- **WHEN** uma transacao CREDIT tiver memo "Pagamento de fatura"
- **THEN** ela e importada normalmente (o pulo vale apenas para DEBIT)

### Requirement: Deduplicacao por FITID
A importacao SHALL registrar cada transacao importada com chave de deduplicacao derivada de conta, FITID e memo, tornando reimportacoes idempotentes; no modo somente novos, item ja importado e pulado, e no modo sobrescrever, lancamento pago nunca e alterado.

#### Scenario: Reimportacao idempotente
- **WHEN** o mesmo arquivo e importado duas vezes no modo somente novos
- **THEN** a segunda importacao nao cria lancamentos e reporta os itens como ja importados

#### Scenario: Sobrescrever nao altera item pago
- **WHEN** o mesmo arquivo e reimportado no modo sobrescrever
- **THEN** lancamentos existentes (pagos desde a criacao) permanecem intactos e sao reportados como ja pagos

### Requirement: Mes aberto obrigatorio
A importacao SHALL exigir que o mes de competencia de todo item novo esteja aberto; havendo qualquer mes fechado, a importacao inteira e cancelada sem gravar nada, informando os meses faltantes.

#### Scenario: Mes fechado cancela tudo
- **WHEN** o arquivo contem transacoes de 06/2026 e 07/2026 e apenas 07/2026 esta aberto
- **THEN** nada e gravado e o erro informa que 06/2026 nao esta aberto

### Requirement: Resultado da importacao
Apos importar, o sistema SHALL exibir resumo com itens criados, atualizados e pulados, incluindo motivo de cada item pulado.

#### Scenario: Resumo apos importacao
- **WHEN** uma importacao termina com sucesso
- **THEN** o usuario ve as contagens e listas de criados, atualizados e pulados com motivos
