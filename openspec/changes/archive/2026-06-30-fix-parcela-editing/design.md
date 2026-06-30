## Context

A edição de parcelas de cartão (`PARCELA_CARTAO`) está falhando durante a submissão do formulário `LancamentoForm`. A causa é a remoção desse tipo de lançamento do conjunto de `choices` do campo `tipo` do formulário (para bloquear cadastro manual) e a validação correspondente no método `clean()`. Quando a requisição POST é realizada, o valor original é rejeitado pelo Django como uma escolha inválida.

## Goals / Non-Goals

**Goals:**
- Permitir a edição bem-sucedida de lançamentos existentes do tipo `PARCELA_CARTAO` e `CONCILIACAO` (como atualização de descrição, valor, conta e data de vencimento).
- Manter o tipo original inalterado durante a edição desses registros.
- Garantir que a criação/cadastro manual de parcelas ou conciliações continue bloqueada.

**Non-Goals:**
- Modificar o fluxo de geração de parcelas (através de `CompraParcelada`).
- Permitir que o usuário converta uma transação comum em parcela de cartão, ou vice-versa.

## Decisions

### Decisão 1: Ajustar `__init__` do `LancamentoForm` para suportar tipos excluídos em instâncias existentes
- **Abordagem:** Verificar se a instância recebida (`self.instance`) já possui um ID salvo (`self.instance.pk` não nulo). Caso o tipo atual da instância esteja contido em `TIPOS_EXCLUIDOS_DO_CADASTRO_MANUAL`, removemos esse tipo temporariamente do conjunto de exclusões apenas para este formulário, para que a escolha seja válida. Adicionalmente, desabilitamos o campo `tipo` (`self.fields["tipo"].disabled = True`).
- **Alternativa Considerada:** Tornar o campo `tipo` oculto ou removê-lo completamente do formulário se for edição de parcela. Contudo, desabilitar o campo é mais limpo no HTML padrão do Django, preserva o rótulo visual do tipo atual e impede modificações indevidas tanto pelo navegador quanto no processamento de submissão do Django.

### Decisão 2: Condicionar validações de tipo no `clean()` para novas instâncias
- **Abordagem:** A validação que gera erros ao detectar `PARCELA_CARTAO` ou `CONCILIACAO` no método `clean()` será executada apenas se `self.instance.pk` for nulo (ou seja, novo cadastro).
- **Alternativa Considerada:** Usar formulários separados para criação e edição. No entanto, os campos e comportamentos são quase idênticos, de modo que estender a lógica condicional no formulário único reduz a duplicação de código e simplifica as rotas na view.

## Risks / Trade-offs

- **[Risco]** Usuário tentar alterar o tipo de um lançamento existente via manipulação de requisição POST.
  - *Mitigação:* Ao definir `disabled = True` no campo do Django, o framework ignora o valor recebido na requisição e reutiliza o valor atual do banco/instância para aquele campo ao salvar o formulário, garantindo segurança na validação do backend.
