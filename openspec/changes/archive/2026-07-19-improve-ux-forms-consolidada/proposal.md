# Melhorar usabilidade dos formularios CRUD e da visao consolidada

## Why

Os formularios de cadastro/edicao esticam na largura total da viewport (o
`.container` nao tem `max-width`), produzindo campos ilegiveis em telas largas.
Varios formularios exibem campos irrelevantes para a selecao atual — as regras
condicionais existem apenas no `clean()` server-side (ex.: conta Cartao proibe
`saldo_atual`, mas o campo aparece sempre), gerando erros de validacao evitaveis.
A visao consolidada empilha sete secoes full-width com os totais enterrados
abaixo da tabela de movimentacoes.

## What Changes

- Largura em duas camadas: `.container` global com `max-width: 1200px` centrado;
  wrapper `.form-page` com `max-width: 600px` nas seis telas de create/edit.
- Grid de duas colunas como padrao nos formularios: campos curtos (datas,
  numeros, moeda) em meia coluna; `descricao` e selects em linha cheia.
- Campos condicionais via JS vanilla declarativo (`data-show-when` +
  `static/js/conditional-fields.js`): campo oculto recebe `disabled` (nao e
  submetido); `clean()` server-side permanece a fonte de verdade.
- Lancamento: tipo dirige conta — APORTE/RESGATE filtra o select para contas
  Investimento; demais tipos escondem Investimento; selecao incompativel e limpa.
- **BREAKING (UI)**: `lancamento_vinculado` sai do formulario de lancamento
  (create e edit). Vinculo passa a ser detalhe interno do fluxo de transferencia;
  na edicao de lancamento vinculado exibe-se apenas info read-only.
- Visao consolidada: totais (Entradas/Saidas/Saldo) sobem como stat-cards no
  topo; navegacao de mes + filtros em barra unica compacta; "Pendentes do mes
  anterior" e "Ajustar saldo inicial" viram secoes colapsaveis fechadas por
  padrao, pendentes com contador + badge quando > 0; acao Pagar vira popover com
  data pre-preenchida. A tabela de movimentacoes mantem estrutura e colunas.
- Polimento leve (container, hierarquia tipografica, chips/stat-cards) em
  Patrimonio, Comparativo e lista de Contas. Desktop-only.

## Capabilities

### New Capabilities
(nenhuma)

### Modified Capabilities
- `frontend-design-system`: novos requisitos de largura contida, layout de
  formulario em grid, campos condicionais por selecao e organizacao da visao
  consolidada (stat-cards, secoes colapsaveis, popover de pagar).
- `lancamentos`: requisito "Campos do lancamento" — vinculo deixa de ser
  informavel pelo formulario; passa a ser estabelecido apenas pelos fluxos do
  sistema (transferencia).

## Impact

- CSS: `static/css/m3-base.css`, `static/css/m3-components.css`.
- JS novo: `static/js/conditional-fields.js` (carregado em `base.html`).
- Templates: `_partials/field.html`, seis telas de form, `consolidada.html`,
  `patrimonio.html`, `comparativo.html`, `contas/lista.html`.
- Forms: `lancamentos/forms.py` (remove `lancamento_vinculado`, expõe
  `data-conta-tipo` nas options), `contas/forms.py` (anotacoes condicionais).
- Sem migracao de banco; modelo e services intactos.
