## 1. Fluxo de contas para usuario final

- [ ] 1.1 Criar `contas/forms.py` com formulario de conta que respeite campos por tipo (Cartao, Banco, Investimento)
- [ ] 1.2 Implementar views e rotas de listar, criar, editar e excluir contas em `contas/views.py` e `contas/urls.py`
- [ ] 1.3 Criar templates de contas e integrar navegacao no layout principal
- [ ] 1.4 Garantir mensagens de erro claras ao bloquear exclusao de conta com lancamentos

## 2. Abertura de mes e tratamento de pendentes

- [ ] 2.1 Ajustar fluxo de abertura para incluir etapa de decisao de pendentes como parte da conclusao da abertura
- [ ] 2.2 Validar transferencia para aceitar apenas lancamentos pendentes do mes imediatamente anterior
- [ ] 2.3 Ajustar endpoints/templates de manter/transferir pendente com feedback de erro quando lancamento nao for elegivel

## 3. Consistencia da visao de conta e filtros de status

- [ ] 3.1 Atualizar calculo de entradas, saidas e saldo para respeitar conta selecionada quando filtro de conta estiver ativo
- [ ] 3.2 Ajustar rotulos de UI para distinguir saldo consolidado de saldo de conta filtrada
- [ ] 3.3 Padronizar filtro de status usando QuerySet para listagem e calculo de saldo

## 4. Restricoes de criacao manual de lancamentos e qualidade

- [ ] 4.1 Remover `PARCELA_CARTAO` das opcoes de criacao manual em `LancamentoForm` (alem de `CONCILIACAO`)
- [ ] 4.2 Garantir mensagem orientando uso de compra parcelada para geracao de parcelas
- [ ] 4.3 Adicionar testes de views/forms para cadastro de contas, transferencia de pendentes e filtro coerente de saldo/status
- [ ] 4.4 Adicionar testes de regressao para impedir criacao manual de `PARCELA_CARTAO`
