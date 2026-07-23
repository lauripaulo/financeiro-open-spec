## Why

Os formulários principais hoje terminam em uma única ação primária, deixando o usuário sem saída explícita para cancelar uma criação/edição ou voltar de um fluxo operacional. A avaliação da UI também mostrou que campos de data reais já usam calendário nativo em boa parte do app, mas a regra precisa ficar verificável para todos os formulários e filtros de competência mês/ano.

## What Changes

- Adicionar ação secundária consistente nos formulários de usuário: `Cancelar` quando há dados editáveis não salvos e `Voltar` em fluxos sem risco de perda de dados.
- Preservar o contexto de origem ao sair de formulários abertos pela Visão consolidada, incluindo mês, conta, status e paginação quando aplicável.
- Padronizar controles de data: datas reais continuam usando `input type="date"`; seletores de mês/ano devem usar um controle de competência mensal mais adequado que dois campos numéricos soltos.
- Melhorar orientação e validação no formulário de Conta para `limite_negativo`, deixando claro que o valor deve ser informado como número positivo e rejeitando valor negativo.
- Manter Material Design 3, sem framework JS novo nem pipeline de build.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `frontend-design-system`: padroniza ações secundárias em formulários e a apresentação de controles de competência mensal.
- `formatacao-data`: reforça que datas reais usam calendário nativo e diferencia data real de competência mês/ano.
- `visualizacao`: preserva contexto de origem nos fluxos iniciados pela Visão consolidada e melhora seleção de mês/ano.
- `contas`: adiciona orientação explícita e validação para preenchimento positivo do limite negativo.

## Impact

- Templates de formulários: `templates/contas/form.html`, `templates/lancamentos/form.html`, `templates/lancamentos/form_edicao.html`, `templates/lancamentos/form_compra_parcelada.html`, `templates/lancamentos/form_transferencia.html`, `templates/importacao/ofx_form.html`.
- Templates de consulta: `templates/visualizacao/consolidada.html`, `templates/visualizacao/planejamento.html`, `templates/visualizacao/comparativo.html`.
- Views que constroem URLs de retorno para criação/edição/importação e preservação de filtros.
- Forms/widgets de data, competência mensal e helper text de `Conta.limite_negativo`.
- Testes de views/templates para presença de `Cancelar`/`Voltar`, `type="date"` e preservação de retorno.
