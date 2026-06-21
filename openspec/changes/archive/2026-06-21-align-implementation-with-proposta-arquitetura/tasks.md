## 1. Fluxo de contas para usuario final

- [x] 1.1 Criar `contas/forms.py` com formulario de conta que respeite campos por tipo (Cartao, Banco, Investimento)
- [x] 1.2 Implementar views e rotas de listar, criar, editar e excluir contas em `contas/views.py` e `contas/urls.py`
- [x] 1.3 Criar templates de contas e integrar navegacao no layout principal
- [x] 1.4 Garantir mensagens de erro claras ao bloquear exclusao de conta com lancamentos

## 2. Abertura de mes e tratamento de pendentes

- [x] 2.1 Ajustar fluxo de abertura para incluir etapa de decisao de pendentes como parte da conclusao da abertura
- [x] 2.2 Validar transferencia para aceitar apenas lancamentos pendentes do mes imediatamente anterior
- [x] 2.3 Ajustar endpoints/templates de manter/transferir pendente com feedback de erro quando lancamento nao for elegivel

## 3. Consistencia da visao de conta e filtros de status

- [x] 3.1 Atualizar calculo de entradas, saidas e saldo para respeitar conta selecionada quando filtro de conta estiver ativo
- [x] 3.2 Ajustar rotulos de UI para distinguir saldo consolidado de saldo de conta filtrada
- [x] 3.3 Padronizar filtro de status usando QuerySet para listagem e calculo de saldo

## 4. Restricoes de criacao manual de lancamentos e qualidade

- [x] 4.1 Remover `PARCELA_CARTAO` das opcoes de criacao manual em `LancamentoForm` (alem de `CONCILIACAO`)
- [x] 4.2 Garantir mensagem orientando uso de compra parcelada para geracao de parcelas
- [x] 4.3 Adicionar testes de views/forms para cadastro de contas, transferencia de pendentes e filtro coerente de saldo/status
- [x] 4.4 Adicionar testes de regressao para impedir criacao manual de `PARCELA_CARTAO`

## 5. Correcao de regressao encontrada durante a implementacao

- [x] 5.1 Corrigir `criar_lancamento` para nao quebrar com `TypeError` ao validar `LancamentoForm`, pois `Lancamento.clean()` acessava `competencia_mes` antes de o valor ser atribuido pela view (campo fora de `LancamentoForm.Meta.fields`)
