## Why

O fluxo de nova compra parcelada hoje sempre gera a serie completa de parcelas e nao permite informar quantas ja foram pagas fora do sistema. Isso nao atende o uso real de migracao de planilha, onde o usuario quer registrar apenas as parcelas que ainda vao vencer, mantendo o total original da compra.

## What Changes

- Adicionar no formulario de compra parcelada o campo `parcelas_pagas`, obrigatorio, com valor inicial `0`.
- Validar `parcelas_pagas` no backend com a regra `0 <= parcelas_pagas <= total_parcelas`.
- Bloquear o cadastro quando `parcelas_pagas == total_parcelas`, com erro de validacao informando que nao ha parcelas a gerar.
- Gerar apenas as parcelas restantes (`total_parcelas - parcelas_pagas`), mantendo numeracao da serie original (`parcela_atual` iniciando em `parcelas_pagas + 1`).
- Manter o calculo de valor por parcela baseado no `valor_total` e `total_parcelas` originais; apenas filtrar os indices gerados.
- Manter a regra de vencimento ancorada em `data_compra`, sem criacao retroativa de parcelas ja pagas.
- Ajustar UX do formulario para sincronizar o `max` de `parcelas_pagas` com `total_parcelas`, incluindo ajuste automatico quando o total diminuir.

## Capabilities

### New Capabilities
- _None._

### Modified Capabilities
- `parcelas`: alterar o comportamento de geracao para suportar compra com parcelas ja pagas e criar somente as parcelas futuras restantes.

## Impact

- Afecta o fluxo de cadastro em `lancamentos/forms.py`, `lancamentos/views.py` e `templates/lancamentos/form_compra_parcelada.html`.
- Afecta a regra de dominio em `parcelas/services.py` para controlar faixa de parcelas geradas.
- Afecta testes de unidade/integracao em `parcelas/tests.py` e possivelmente `lancamentos/tests.py`.
- Nao introduz mudanca de API externa nem dependencia nova.
- Nao exige migracao de banco nesta iteracao (campo `parcelas_pagas` permanece apenas no formulario/servico).
