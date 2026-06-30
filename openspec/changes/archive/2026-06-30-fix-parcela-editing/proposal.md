## Why

A edição de lançamentos do tipo Parcela de Cartão (`PARCELA_CARTAO`) está quebrada devido a restrições no formulário `LancamentoForm` que foram originalmente projetadas apenas para o cadastro manual (criação). Isso impede que o usuário altere valores, datas de vencimento ou descrições de parcelas específicas após terem sido geradas.

## What Changes

- Ajustar o formulário `LancamentoForm` para aceitar a validação e renderização correta de lançamentos do tipo `PARCELA_CARTAO` e `CONCILIACAO` durante a edição (quando `self.instance.pk` já está definido).
- Desabilitar o campo `tipo` (`disabled=True`) ao editar transações que possuem tipos protegidos (`PARCELA_CARTAO` e `CONCILIACAO`), garantindo que o tipo da transação permaneça imutável.
- Limitar a validação que bloqueia a criação manual de `PARCELA_CARTAO` e `CONCILIACAO` no método `clean()` do formulário apenas para novas instâncias (`if not self.instance.pk`).

## Capabilities

### New Capabilities
- *None.*

### Modified Capabilities
- `lancamentos`: Ajustar as restrições de tipos especiais para permitir a edição de lançamentos existentes do tipo Parcela de Cartão e Conciliação, mantendo o tipo imutável no formulário.

## Impact

- Afeta o formulário `LancamentoForm` em `lancamentos/forms.py`.
- Adiciona cenários de teste de edição de parcelas de cartão e conciliação em `lancamentos/tests.py` para garantir que o formulário de edição funcione adequadamente.
