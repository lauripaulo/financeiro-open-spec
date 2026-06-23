## Why

Clicking "Gerar parcelas" on the compra-parcelada form appears to do nothing: the parcelas are actually created correctly in the database, but the view unconditionally returns an empty `204 No Content` response to what is a plain (non-htmx) form submission, so the browser never navigates anywhere and the page looks frozen. Even if the response were fixed, the "Nova compra parcelada" link never carries the month the user was viewing, so there'd be nothing to return to — the user must land back on the same month they came from, not today's month or the purchase month.

## What Changes

- The "Nova compra parcelada" link on the consolidated view now carries `?ano={{ ano }}&mes={{ mes }}`, the same convention already used by the adjacent "Novo lancamento" link.
- `criar_compra_parcelada` reads that month context via the existing `_contexto_mes(request)` helper (already used by `criar_lancamento`) instead of ignoring it.
- On a successful plain (non-htmx) submit, the view redirects back to the consolidated view for that same `ano`/`mes` instead of returning a bare `204`; on an htmx request it keeps returning `204` (mirroring `criar_lancamento`'s existing branch).
- The redirect target is always the month the user came from — never the purchase date's month, never the first parcela's month, never "today".

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `visualizacao`: adds a requirement that registering a lancamento or compra parcelada returns the user to the month they were viewing when they opened the form.

## Impact

- Template: `templates/visualizacao/consolidada.html` (the "Nova compra parcelada" link).
- View: `lancamentos/views.py` (`criar_compra_parcelada`).
- No model/database changes. No new dependencies.
