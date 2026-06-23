## 1. Button styling for primary action links

- [x] 1.1 Add `a.button` / `a.button.secondary` CSS rules to `templates/base.html`, reusing the existing `button` / `button.secondary` color scheme
- [x] 1.2 Apply `class="button"` to "Novo lancamento", "Nova compra parcelada" and "Editar" in `templates/visualizacao/consolidada.html`
- [x] 1.3 Apply `class="button"` to "Nova conta" and "Editar" in `templates/contas/lista.html`
- [x] 1.4 Apply `class="button"` to "Concluir abertura e ir para a visao consolidada" in `templates/visualizacao/resolver_pendentes.html`

## 2. Confirmation before exclusion

- [x] 2.1 Add `hx-confirm` to the htmx exclusion form for lancamentos in `templates/visualizacao/consolidada.html`
- [x] 2.2 Add `onsubmit="return confirm(...)"` to the plain exclusion form for contas in `templates/contas/lista.html`
- [x] 2.3 Leave `_confirmar_excluir_par.html` (linked-lancamento exclusion) unchanged — it already implements a deliberate two-step confirmation

## 3. Full-page refresh after non-navigating actions

- [x] 3.1 Add `from django.contrib import messages` to `lancamentos/views.py` and `visualizacao/views.py`
- [x] 3.2 Update `marcar_pago`, `excluir_lancamento`, `excluir_lancamento_par` in `lancamentos/views.py` to call `messages.success` and return `HttpResponse(status=204, headers={"HX-Refresh": "true"})`
- [x] 3.3 Update `transferir_pendente`, `manter_pendente`, `ajustar_saldo` in `visualizacao/views.py` to use `messages.success`/keep `HttpResponseBadRequest` for validation errors, and return `HttpResponse(status=204, headers={"HX-Refresh": "true"})` on success instead of rendering `_flash.html`
- [x] 3.4 Render `{% for message in messages %}` inside `#flash-area` in `templates/base.html` so messages persist across the forced reload
- [x] 3.5 Fix `editar_lancamento` in `lancamentos/views.py` to redirect back to the consolidated view on a successful plain (non-htmx) form submit, instead of returning an empty `204`

## 4. Tests

- [x] 4.1 Update `visualizacao/tests.py` assertions for `transferir_pendente`, `manter_pendente`, `ajustar_saldo` to expect `204` + `HX-Refresh: true` instead of `200` + rendered `_flash.html`
- [x] 4.2 Run full test suite (`python manage.py test`) and confirm all tests pass
- [x] 4.3 Manually verify against the dev server: button styling renders, `hx-confirm`/`onsubmit` confirmation dialogs appear, and a delete shows the "Lancamento excluido." message after the forced page refresh
