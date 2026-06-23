## 1. Aplicar regras de sequencia na abertura de mes

- [x] 1.1 Adicionar validacao no service layer em `meses/services.py` para permitir somente o mes atual como primeiro mes aberto
- [x] 1.2 Adicionar validacao no service layer em `meses/services.py` para permitir somente o mes imediatamente seguinte ao ultimo mes aberto
- [x] 1.3 Manter comportamento idempotente quando `criar_mes` for chamado para um mes ja aberto
- [x] 1.4 Retornar mensagem de validacao clara contendo o mes permitido (`MM/AAAA`) quando a sequencia for violada

## 2. Tornar parcelas exclusivas do fluxo de compra

- [x] 2.1 Remover o ramo de propagacao de `PARCELA_CARTAO` da logica de abertura de mes em `meses/services.py`
- [x] 2.2 Garantir que a propagacao de mes continue cobrindo tipos recorrentes fixos (`RECEBIMENTO_FIXO`, `GASTO_FIXO`, `ASSINATURA`)
- [x] 2.3 Manter a geracao de parcelas centralizada no fluxo de compra em `parcelas/services.py`

## 3. Alinhar semantica de recorrencia de lancamentos

- [x] 3.1 Remover `PARCELA_CARTAO` da classificacao de recorrencia (`TIPOS_PROPAGAVEIS`) em `lancamentos/models.py`
- [x] 3.2 Verificar que a cascata de edicao recorrente (`atualizar_serie_futura`) nao aplica mais atualizacoes em massa para parcelas
- [x] 3.3 Verificar que a cascata de exclusao recorrente (`excluir_serie_futura`) nao remove mais parcelas como serie recorrente

## 4. Atualizar feedback de abertura de mes na visualizacao

- [x] 4.1 Tratar erros de validacao de abertura de mes em `visualizacao/views.py` e expor feedback claro para o usuario
- [x] 4.2 Atualizar `templates/visualizacao/mes_nao_criado.html` para mostrar o mes permitido e o proximo passo acionavel
- [x] 4.3 Garantir que o fluxo consolidado mantenha navegacao coerente quando a criacao de mes for rejeitada pelas regras de sequencia

## 5. Expandir e adaptar testes

- [x] 5.1 Adicionar testes em `meses/tests.py` para garantir que o primeiro mes deve ser o atual
- [x] 5.2 Adicionar testes em `meses/tests.py` para validar regra estrita de nao pular mes e caso de sucesso do mes imediatamente seguinte
- [x] 5.3 Adicionar teste de regressao provando que abrir mes nao cria parcelas duplicadas apos geracao por compra
- [x] 5.4 Atualizar testes afetados em `visualizacao/tests.py` para o comportamento de feedback da validacao de sequencia
- [x] 5.5 Refatorar testes sensiveis a data para ficarem deterministas sob a regra de primeiro mes atual

## 6. Atualizar specs e documentacao

- [x] 6.1 Validar os deltas de spec de `meses`, `parcelas`, `lancamentos` e `visualizacao` com `openspec validate`
- [x] 6.2 Alinhar a redacao da documentacao do projeto com a responsabilidade canonica de parcelas e a regra sequencial de abertura de mes
- [x] 6.3 Atualizar `README.md` como etapa final da execucao para refletir o novo comportamento e corrigir exemplos de comandos OpenSpec
