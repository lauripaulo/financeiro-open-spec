# Formatacao de Data

## Purpose
Definir o padrao de exibicao de datas e o comportamento dos campos de entrada de data no sistema.

## Requirements

### Requirement: Exibicao de datas no padrao brasileiro
Toda data exibida em tela (data de vencimento, data de pagamento, data de compra, datas em listagens e historico) SHALL ser formatada no padrao `dd/mm/aaaa`.

#### Scenario: Data de vencimento exibida na visao consolidada
- GIVEN um lancamento com data de vencimento 2026-06-05
- WHEN a visao consolidada exibe esse lancamento
- THEN o sistema SHALL exibir a data como "05/06/2026"

### Requirement: Campo de entrada de data com calendario nativo
Todo campo de entrada de data do sistema (data de vencimento do lancamento, data de pagamento, data da compra parcelada) SHALL usar um campo de entrada de data nativo (`type="date"`), exibindo o seletor de calendario do navegador como padrao, em vez de um campo de texto livre.

#### Scenario: Usuario informa a data de vencimento de um novo lancamento
- GIVEN o usuario esta cadastrando um novo lancamento
- WHEN ele abre o campo de Data de vencimento
- THEN o sistema SHALL exibir um seletor de calendario nativo do navegador
- AND a data digitada ou selecionada SHALL ser exibida no formato dd/mm/aaaa

#### Scenario: Edicao de lancamento preenche o campo de data corretamente
- GIVEN um lancamento existente com data de vencimento 2026-06-05
- WHEN o usuario abre o formulario de edicao desse lancamento
- THEN o campo de Data de vencimento SHALL exibir essa data preenchida corretamente
- AND SHALL permanecer compativel com o seletor de calendario nativo

#### Scenario: Usuario informa a data de uma compra parcelada
- GIVEN o usuario esta registrando uma nova compra parcelada
- WHEN ele abre o campo de Data da compra
- THEN o sistema SHALL exibir um seletor de calendario nativo do navegador
