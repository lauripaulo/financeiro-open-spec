## Context

The app is a server-rendered Django app with htmx (1.9.12) loaded globally but used selectively per-form. Action buttons are styled with plain CSS classes on `<button>` (`button`, `button.secondary`); `<a>` tags have no equivalent styling. Several htmx-enabled POST actions return either `204 No Content` or a rendered partial (`_flash.html`) targeted at `#flash-area`, but none of them update the rest of the page, so the table/list the action just affected goes stale until a manual reload. No delete action anywhere in the app asks for confirmation except the one bespoke "linked lancamento" screen (`_confirmar_excluir_par.html`).

## Goals / Non-Goals

**Goals:**
- Primary action links look and behave like buttons, reusing existing CSS rather than introducing a new design system.
- Every destructive (exclusion) action requires explicit confirmation before executing.
- Every action that doesn't navigate to a new URL leaves the page in a correct, up-to-date state without requiring a manual reload.
- Reuse Django's already-configured `messages` framework (app, middleware, context processor all present) instead of inventing a parallel flash mechanism.

**Non-Goals:**
- No new design system, no CSS framework adoption (Bootstrap, Tailwind, etc.).
- No change to the bespoke linked-lancamento delete confirmation screen (`_confirmar_excluir_par.html`) — it already satisfies "confirmation before exclusion" via a deliberate two-choice step.
- No attempt to support a no-JS fallback for the htmx-only actions (this was already unsupported before this change).

## Decisions

- **Button styling via a shared CSS class, not inline styles.** Add `a.button` / `a.button.secondary` selectors in `base.html` alongside the existing `button` / `button.secondary` rules, then apply `class="button"` to the relevant anchors. Alternative considered: wrap each link in a `<form>` with a `<button>` — rejected because it changes semantics (forms imply POST) and bloats markup for what's just a navigation link.
- **Confirmation via `hx-confirm` for htmx forms, native `onsubmit="return confirm(...)"` for plain forms.** htmx already ships `hx-confirm` (browser-native `confirm()` under the hood) which is the lowest-friction option requiring no new JS. The one plain (non-htmx) delete form (`contas/lista.html`) doesn't fire through htmx, so it needs the vanilla `onsubmit` attribute instead.
- **Full-page refresh via `HX-Refresh: true` response header, not manual DOM patching.** htmx natively supports this header to force a full `window.location.reload()`, which is simpler and more robust than writing per-action JS to patch the affected table row out, in, or updated. Alternative considered: re-render and swap the entire content block via `hx-target="body"` — rejected as a much larger diff for marginal UX gain (no partial-page transition value here, since these are simple CRUD-style actions).
- **Move flash messages to Django's `messages` framework.** Because `HX-Refresh` immediately discards the response body, the existing pattern of rendering `_flash.html` into `#flash-area` no longer works — the browser navigates away before the user can see it. `django.contrib.messages` persists messages in a cookie/session across the reload, and `base.html` already has a natural place to render them (`#flash-area`). This is already-installed infrastructure, not a new dependency.
- **Fix `editar_lancamento`'s missing redirect as part of this change, not a separate one.** It's the same class of bug (action that doesn't navigate when it should) discovered during implementation; the fix is one line and shares the same root cause as the rest of this change.

## Risks / Trade-offs

- [Risk] `HX-Refresh: true` causes a full page reload, which is slightly heavier than a targeted DOM patch and briefly flashes a loading state. → Mitigation: acceptable for this app's scale (personal finance tracker, small per-page row counts); consistent behavior outweighs the minor perf cost.
- [Risk] Switching `transferir_pendente`/`manter_pendente`/`ajustar_saldo` from `200` + rendered partial to `204` + `HX-Refresh` is a breaking response-contract change for those three endpoints. → Mitigation: they're only consumed by this app's own templates (no external API contract); existing tests updated to match.
- [Risk] Native `confirm()` dialogs are not visually consistent with the app's own styling and block the main thread. → Mitigation: acceptable trade-off for the scope of this change; a custom modal confirmation is out of scope (see Non-Goals).

## Migration Plan

No data migration. Deploy is just code (templates + views); existing message middleware/session config already supports `django.contrib.messages`. Rollback is a plain revert of the commit(s).
