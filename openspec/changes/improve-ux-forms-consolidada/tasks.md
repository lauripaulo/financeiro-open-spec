# Tasks — improve-ux-forms-consolidada

## 1. Fundacao CSS

- [x] 1.1 `static/css/m3-base.css`: `max-width: 1200px` no `.container`
- [x] 1.2 `static/css/m3-components.css`: `.form-page` (max-width 600px, margin
      auto), `.form-grid` (grid 2 colunas, gap), `.form-grid__full` (span 2)
- [x] 1.3 `.m3-stat-card` / `.m3-stat-row` para totais da consolidada
- [x] 1.4 Estilo de `<details>` colapsavel (`.m3-collapsible`) + badge de
      contagem no summary
- [x] 1.5 Estilo do popover de pagar (`.m3-popover`)

## 2. Layout dos formularios

- [x] 2.1 `templates/_partials/field.html`: suportar span (cheio vs meia coluna)
      e atributos `data-show-when`
- [x] 2.2 Aplicar `.form-page` + `.form-grid` em `contas/form.html`
- [x] 2.3 Aplicar em `lancamentos/form.html` e `form_edicao.html`
- [x] 2.4 Aplicar em `form_compra_parcelada.html` e `form_transferencia.html`

## 3. Campos condicionais

- [x] 3.1 Criar `static/js/conditional-fields.js` (le `data-show-when`,
      esconde+disabled / mostra+reabilita, roda no load) e carregar em
      `base.html`
- [x] 3.2 Anotar condicionais do ContaForm (tabela do design.md)
- [x] 3.3 `lancamentos/forms.py`: remover `lancamento_vinculado` dos fields;
      widget Select com `data-conta-tipo` nas options de conta
- [x] 3.4 Filtro tipo→conta no JS (esconde options incompativeis, limpa selecao)
- [x] 3.5 `form_edicao.html`: bloco read-only "vinculado a X" quando houver par
- [x] 3.6 Ajustar/adicionar testes de form (field removido; submit sem campos
      disabled passa clean())

## 4. Visao consolidada

- [x] 4.1 Stat-cards Entradas/Saidas/Saldo no topo; remover card Totais do fim
- [x] 4.2 Barra unica: navegacao de mes + filtros compactos
- [x] 4.3 `<details>` fechado para Pendentes (summary com contador + badge
      quando > 0) e Ajustar saldo inicial
- [x] 4.4 Popover de pagar substituindo o form inline (mesmo POST HTMX
      `marcar_pago`, data default = hoje)
- [x] 4.5 Tabela de movimentacoes: estrutura e colunas intocadas

## 5. Polimento leve

- [x] 5.1 `patrimonio.html`: hierarquia tipografica + stat-cards onde couber
- [x] 5.2 `comparativo.html`: idem
- [x] 5.3 `contas/lista.html`: idem

## 6. Docs

- [x] 6.1 Criar `CONTEXT.md` com glossario inicial (ver design.md)

## 7. Verificacao

- [x] 7.1 `manage.py test` completo
- [x] 7.2 Smoke manual nas 6 telas de form (alternar tipos, submits validos,
      editar Banco→Cartao salva sem erro invisivel)
- [x] 7.3 Consolidada: stat-cards, colapsaveis, popover pagar, tabela legivel
- [x] 7.4 `openspec validate --changes`
