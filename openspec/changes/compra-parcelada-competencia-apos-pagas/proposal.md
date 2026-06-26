## Why

Ao cadastrar compra parcelada com `parcelas_pagas > 0`, a implementacao atual esta deslocando a competencia e o vencimento para frente com base no indice original da parcela. Isso viola a expectativa do usuario de comecar o planejamento das parcelas restantes no mes seguinte a data da compra.

## What Changes

- Corrigir a regra de calendario para compras parceladas com `parcelas_pagas > 0`.
- Fazer a primeira parcela gerada (mesmo que numerada como `N/total`) usar competencia e vencimento do mes seguinte a `data_compra`.
- Manter numeracao original da serie (`parcela_atual` e descricao `N/total`) sem pular meses na competencia.
- Preservar calculo financeiro atual baseado em `valor_total` e `total_parcelas` originais.
- Ajustar testes para validar a nova ancora temporal de `competencia_ano/mes` e `data_vencimento`.

## Capabilities

### New Capabilities
- _None._

### Modified Capabilities
- `parcelas`: alterar o comportamento de calendario na geracao parcial para que as parcelas restantes iniciem no mes seguinte da compra, mantendo numeracao original.

## Impact

- Afecta a logica de geracao em `parcelas/services.py`.
- Afecta testes de comportamento em `parcelas/tests.py`.
- Nao exige migracao de banco, novas dependencias ou mudancas de API externa.
