## 1. Modelo

- [ ] 1.1 Adicionar campo `lancamento_vinculado = FK('self', null=True, blank=True, on_delete=SET_NULL, related_name='lancamento_par')` ao modelo `Lancamento` em `lancamentos/models.py`
- [ ] 1.2 Gerar e aplicar migração de banco de dados para o novo campo
- [ ] 1.3 Implementar sincronização bidirecional no `Lancamento.save()`: ao definir `lancamento_vinculado`, verificar se o lado oposto já aponta de volta; se não apontar, atualizar via `update_fields=['lancamento_vinculado']` com guard de ciclo
- [ ] 1.4 Implementar limpeza do vínculo anterior no `Lancamento.save()`: quando `lancamento_vinculado` muda de B para C (ou para null), limpar `B.lancamento_vinculado` antes de setar o novo
- [ ] 1.5 Implementar validação em `Lancamento.clean()`: quando `lancamento_vinculado` está definido, verificar que `abs(self.valor) == abs(self.lancamento_vinculado.valor)` e lançar `ValidationError` se diferirem

## 2. Formulários

- [ ] 2.1 Adicionar campo `lancamento_vinculado` ao `LancamentoForm` em `lancamentos/forms.py` como campo opcional, com queryset excluindo o próprio lançamento e lançamentos já vinculados a outro par
- [ ] 2.2 Adicionar validação no `LancamentoForm.clean()` para verificar igualdade de valor absoluto ao vincular, exibindo mensagem de erro clara ao usuário

## 3. Exclusão com aviso de par vinculado

- [ ] 3.1 Atualizar a view de exclusão de lançamento em `lancamentos/views.py` para verificar `lancamento.lancamento_vinculado` antes de processar o DELETE
- [ ] 3.2 Renderizar tela de confirmação com as duas opções quando par vinculado existir: "Excluir somente este lançamento" e "Excluir este lançamento e o lançamento vinculado"
- [ ] 3.3 Implementar rota/ação para "excluir os dois": excluir o par vinculado e em seguida o lançamento original

## 4. Visão Consolidada

- [ ] 4.1 Atualizar query em `visualizacao/views.py` para incluir `select_related('lancamento_vinculado__conta')` nos lançamentos da visão consolidada
- [ ] 4.2 Adicionar coluna "Contraparte" ao template `visualizacao/consolidada.html`, exibindo `→ <conta.nome>` quando `lancamento.lancamento_vinculado` existir e a conta contraparte for do tipo Investimento ou `← <conta.nome>` quando for uma entrada proveniente de Investimento; deixar vazia quando não houver vínculo

## 5. Visão Patrimônio

- [ ] 5.1 Atualizar query em `visualizacao/views.py` para incluir `select_related('lancamento_vinculado__conta')` nos movimentos da visão patrimônio
- [ ] 5.2 Adicionar coluna de conta bancária ao template `visualizacao/patrimonio.html`, exibindo `lancamento.lancamento_vinculado.conta.nome` para cada aporte/resgate vinculado; deixar vazia quando não houver vínculo

## 6. Testes

- [ ] 6.1 Testar que setar `A.lancamento_vinculado = B` sincroniza `B.lancamento_vinculado = A` automaticamente
- [ ] 6.2 Testar que trocar `A.lancamento_vinculado` de B para C limpa `B.lancamento_vinculado` e define `C.lancamento_vinculado = A`
- [ ] 6.3 Testar que remover `A.lancamento_vinculado` (setar para null) limpa `B.lancamento_vinculado`
- [ ] 6.4 Testar que vínculo entre lançamentos com valores absolutos diferentes lança `ValidationError`
- [ ] 6.5 Testar que vínculo entre lançamentos com mesmo valor absoluto é aceito
- [ ] 6.6 Testar que a view de exclusão exibe aviso quando o lançamento possui par vinculado
- [ ] 6.7 Testar que "excluir os dois" remove ambos os lançamentos do par
- [ ] 6.8 Testar que "excluir somente este" remove apenas o lançamento e limpa o vínculo do par sobrevivente
- [ ] 6.9 Testar que a visão consolidada inclui a conta contraparte nos lançamentos vinculados
- [ ] 6.10 Testar que a visão patrimônio exibe a conta bancária para aportes e resgates vinculados
