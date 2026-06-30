## 1. Implementação do Formulário

- [x] 1.1 Atualizar o método `__init__` do formulário `LancamentoForm` em `lancamentos/forms.py` para não remover tipos excluídos (como `PARCELA_CARTAO` e `CONCILIACAO`) quando o formulário estiver editando uma instância existente deste tipo.
- [x] 1.2 No mesmo `__init__`, marcar o campo `tipo` como `disabled = True` quando for edição de lançamento existente cujo tipo atual esteja em `TIPOS_EXCLUIDOS_DO_CADASTRO_MANUAL`.
- [x] 1.3 Atualizar o método `clean` do formulário `LancamentoForm` em `lancamentos/forms.py` para executar os blocos de erro de `CONCILIACAO` e `PARCELA_CARTAO` apenas para novos registros (`if not self.instance.pk`).

## 2. Testes de Unidade

- [x] 2.1 Adicionar teste em `lancamentos/tests.py` para validar que o formulário `LancamentoForm` aceita e valida com sucesso a edição de um lançamento de tipo `PARCELA_CARTAO` (mantendo o tipo original e atualizando outros campos como valor e descrição).
- [x] 2.2 Adicionar teste em `lancamentos/tests.py` para validar que ao editar um `PARCELA_CARTAO` o campo `tipo` fica desabilitado no formulário, impedindo alterações do tipo da transação.
- [x] 2.3 Executar a suíte completa de testes (`python manage.py test`) para garantir que todos os testes existentes e novos continuem passando sem regressões.
