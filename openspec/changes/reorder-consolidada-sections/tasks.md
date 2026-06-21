## 1. Reordenar secoes na Visao consolidada

- [x] 1.1 Mover o bloco `<section><h3>Movimentacoes</h3>...</section>` para imediatamente depois do bloco `Filtros` em `templates/visualizacao/consolidada.html`
- [x] 1.2 Posicionar o bloco `Totais` imediatamente depois de `Movimentacoes`
- [x] 1.3 Posicionar o bloco `Pendentes do mes anterior` depois de `Totais`
- [x] 1.4 Mover o bloco `Ajustar saldo inicial (Banco/Cartao)` para o final da pagina
- [ ] 1.5 Validar manualmente a nova ordem das secoes na tela e confirmar que os formularios HTMX (Ajustar saldo, Transferir/Manter pendente, Pagar/Editar/Excluir lancamento) continuam funcionando
- [x] 1.6 Rodar `python manage.py test` para garantir que nao ha regressao
