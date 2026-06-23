## Context

`templates/lancamentos/form_compra_parcelada.html` is a plain `<form method="post">` with no `hx-post`/`hx-boost` — same as `templates/lancamentos/form.html` (the "Novo lancamento" form). `criar_lancamento` already handles this correctly: it reads the origin month via `_contexto_mes(request)` (which pulls `ano`/`mes` from `request.GET`, working on both the initial GET and the POST because the form has no `action` attribute and so resubmits to the same URL, query string included) and redirects to `f"/?ano={ano}&mes={mes}"` on success for plain requests, only returning `204` when `HX-Request` is present.

`criar_compra_parcelada` never adopted this pattern: it ignores month context entirely and unconditionally returns `204`. Verified via direct POST that the parcelas are created correctly server-side (5/5 `Lancamento` rows written with correct months/values) — the bug is purely in the response, not the domain logic. This is the same bug class fixed for `editar_lancamento` in the `ui-action-consistency` change.

## Goals / Non-Goals

**Goals:**
- "Gerar parcelas" behaves identically to "Novo lancamento": after a successful plain submit, the browser navigates back to the consolidated view for the month the user came from.
- The origin month is always the one being viewed when "Nova compra parcelada" was clicked — never the purchase date's month, never the first parcela's month.

**Non-Goals:**
- No change to parcela generation logic (`parcelas/services.py`) — already correct.
- No change to the htmx-request branch's behavior (still returns `204`); this change only fixes the plain-submit path, since the template has no htmx wiring today and adding any isn't needed to fix the reported bug.

## Decisions

- **Reuse `_contexto_mes(request)` and the `?ano=&mes=` query-string convention verbatim**, rather than inventing a new mechanism (e.g. a hidden form field). The convention already round-trips correctly through GET → form (no `action`) → POST for `criar_lancamento`, so applying the identical pattern to `criar_compra_parcelada` is the smallest, most consistent fix and needs no template restructuring beyond adding the query string to the link.
- **Add the redirect/204 branch to `criar_compra_parcelada` exactly mirroring `criar_lancamento`'s `if request.headers.get("HX-Request"): return HttpResponse(status=204)` / `return redirect(...)` structure.** Keeps the two "create and go back" flows symmetric, which matters since they sit right next to each other in the same view module and template.
- **Always redirect to the origin month, never the purchase month.** Confirmed explicitly with the user — a compra dated in March viewed from July's screen must return to July, not March, since "month being edited" refers to where the user is working, not the transaction date.

## Risks / Trade-offs

- [Risk] If a user reaches `/lancamentos/parcelado/` directly (no `?ano=&mes=` in the URL, e.g. a bookmarked link), `_contexto_mes` already falls back to today's year/month (its existing default behavior for `criar_lancamento`), so the redirect still lands somewhere sensible rather than failing. → No mitigation needed, this is existing, accepted behavior.

## Migration Plan

No data migration. Pure view + template change. Rollback is a plain revert.
