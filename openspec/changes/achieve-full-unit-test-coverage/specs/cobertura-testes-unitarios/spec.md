## ADDED Requirements

### Requirement: Cobertura total de testes unitarios
Todo modulo Python do projeto SHALL ser coberto por testes unitarios suficientes para alcancar 100% de cobertura de instrucoes (statement coverage). O comando de verificacao SHALL executar todos os testes e reportar 0 (zero) instrucoes nao cobertas.

#### Scenario: Relatorio de cobertura mostra 100%
- **WHEN** o comando `.venv/bin/coverage run manage.py test` e executado com sucesso
- **THEN** `.venv/bin/coverage report -m` SHALL reportar `TOTAL` com `100%` de cobertura e nenhuma linha na coluna `Missing`
- **AND** nenhum modulo Python relevante SHALL aparecer com menos de 100%

#### Scenario: Cobertura permanece apos mudancas futuras
- **WHEN** novas instrucoes forem adicionadas ao codigo de producao
- **THEN** elas SHALL ser acompanhadas de testes que as executem
- **AND** o comando de cobertura local/CI SHALL continuar reportando 100%

### Requirement: Linhas nao cobertas atuais sao testadas ou removidas
Toda instrucao atualmente listada como `Missing` no relatorio de cobertura SHALL ser coberta por um novo teste unitario, exceto quando for provadamente codigo morto, que SHALL ser removido.

#### Scenario: Branches defensivos recebem testes
- **WHEN** uma linha `Missing` representa um caminho defensivo valido (ex: entrada invalida, validacao de ausencia de campo, URL externa rejeitada)
- **THEN** um teste unitario correspondente SHALL ser adicionado
- **AND** a linha passa a ser reportada como coberta

#### Scenario: Codigo morto e removido
- **WHEN** uma linha `Missing` nao puder ser alcancada por nenhum fluxo real
- **THEN** ela SHALL ser removida ou simplificada
- **AND** a suite de testes continua passando
