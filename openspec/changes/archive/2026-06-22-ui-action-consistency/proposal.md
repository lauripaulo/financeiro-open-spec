## Why

Action elements (links and buttons) across the app are visually and behaviorally inconsistent: primary actions like "Editar" or "Novo lancamento" render as plain text links instead of buttons, most exclusion buttons fire immediately with no confirmation, and several htmx-powered actions (Pagar, Excluir, Transferir, Manter, Ajustar saldo) only swap a flash message into `#flash-area` without updating the rest of the page — so a deleted row, for example, stays visible until the user manually reloads. This was implemented directly in a prior session; this change formalizes it as specs so the behavior is documented and testable going forward.

## What Changes

- Primary-action links (`Novo lancamento`, `Nova compra parcelada`, `Editar`, `Nova conta`, "Concluir abertura...") are styled as buttons using a shared `.button`/`.button.secondary` CSS class, consistent with existing `<button>` styling.
- Every exclusion action (lancamento, lancamento vinculado, conta) requires explicit user confirmation before it executes, either via `hx-confirm` (htmx actions) or a native `confirm()` on plain form submits.
- Every action that completes without navigating to a new URL (Pagar, Excluir, Transferir pendente, Manter pendente, Ajustar saldo) now triggers a full page refresh afterward, so the visible table/list always reflects the latest state. Success/error feedback for these actions is now delivered via Django's messages framework so it survives the refresh.
- **BREAKING (internal only)**: these htmx endpoints now return `204` with an `HX-Refresh: true` header instead of rendering a flash partial into `#flash-area`; any other client relying on the old partial-render response would need to adapt.
- Bug fix: editing a lancamento via the plain (non-htmx) form previously returned an empty `204` response with no redirect, leaving the user stuck on the form with no feedback; it now redirects back to the consolidated view on success.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `visualizacao`: "Indicacao de status e acoes por lancamento" gains confirmation-before-exclusion and refresh-after-action requirements; primary action links must be styled as buttons.
- `contas`: "Cadastro de contas no fluxo principal da aplicacao" gains a confirmation-before-exclusion requirement for the contas list screen.

## Impact

- Templates: `templates/base.html`, `templates/visualizacao/consolidada.html`, `templates/visualizacao/resolver_pendentes.html`, `templates/contas/lista.html`.
- Views: `lancamentos/views.py` (`marcar_pago`, `excluir_lancamento`, `excluir_lancamento_par`, `editar_lancamento`), `visualizacao/views.py` (`transferir_pendente`, `manter_pendente`, `ajustar_saldo`).
- Tests: `visualizacao/tests.py` updated to assert `204` + `HX-Refresh: true` instead of `200` + rendered flash partial.
- No database/model changes.
