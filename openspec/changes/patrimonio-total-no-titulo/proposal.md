## Why

A Visao de patrimonio hoje mostra o saldo acumulado por conta, mas nao exibe um total consolidado no cabecalho da propria tela. Isso dificulta a leitura rapida do patrimonio total investido sem precisar somar manualmente os valores das contas.

## What Changes

- Exibir no titulo da Visao de patrimonio o total consolidado de todas as contas de investimento.
- Usar o formato textual acordado: `Visao de patrimonio: Total R$ X.XXX,XX`.
- Calcular o total como soma dos mesmos saldos acumulados ja exibidos por conta na tela.
- Mostrar total `R$ 0,00` quando nao houver contas de investimento.
- Cobrir o comportamento com testes da view/template.

## Capabilities

### New Capabilities
- _None._

### Modified Capabilities
- `visualizacao`: ajustar a Visao de patrimonio para exibir no titulo o total consolidado das contas de investimento.

## Impact

- Afecta `visualizacao/views.py` (calculo e envio do total para o template).
- Afecta `templates/visualizacao/patrimonio.html` (renderizacao do titulo com total).
- Afecta `visualizacao/tests.py` (novos cenarios para total consolidado e caso sem contas).
- Nao exige migracao de banco, alteracao de API externa ou nova dependencia.
