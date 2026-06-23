## Context

`LANGUAGE_CODE = 'pt-br'` is already set in `financeiro/settings.py`, and Django 5.2 always applies locale-aware formatting (the `USE_L10N` switch was removed; localization is on by default). The "Pagar" inline date field on the consolidated view already uses a hand-written `<input type="date" name="data_pagamento">`, which browsers render with the pt-BR locale's dd/mm/yyyy display and a native calendar — this is the reference behavior shown in the screenshot. The other date fields (`LancamentoForm.data_vencimento`, `CompraParceladaForm.data_compra`) are plain Django `forms.DateField` instances rendered via `{{ form.as_p }}`, which default to a free-text `DateInput` widget with no calendar and no format enforcement.

## Goals / Non-Goals

**Goals:**
- Every date entry field in the app uses the native HTML5 `type="date"` input, so the browser supplies the calendar picker and the dd/mm/yyyy display for free (no new JS dependency).
- Existing values (e.g. editing a lancamento) populate the date input correctly regardless of Django's locale-aware formatting.

**Non-Goals:**
- No custom JS calendar widget (e.g. flatpickr) — the native browser picker already matches the screenshot.
- No change to read-only date displays (tables), which already use `|date:"d/m/Y"` and are already correct.
- No change to `dia_vencimento` (an integer day-of-month on `Conta`, not a date).

## Decisions

- **Use `forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")` rather than relying on Django's default `DateInput`.** HTML5 `type="date"` strictly requires the `value` attribute to be ISO-8601 (`yyyy-mm-dd`); if `format` isn't pinned, Django's locale-aware rendering (pt-br) would emit `dd/mm/yyyy` into the `value` attribute when editing an existing record, which browsers reject for `type="date"` (the field would silently render empty). Pinning `format="%Y-%m-%d"` on the widget keeps the wire format ISO while the browser still *displays* it as dd/mm/yyyy per its own locale — exactly the same mechanism already working for the "Pagar" field.
- **Apply this at the widget level in `lancamentos/forms.py`, not via template changes.** All three affected forms (`LancamentoForm`, `CompraParceladaForm`, `MarcarPagoForm`) are rendered with `{{ form.as_p }}` or constructed directly; fixing the widget once per field is sufic and keeps templates untouched.
- **Also fix `MarcarPagoForm.data_pagamento`'s widget for consistency**, even though the current template hand-writes the `<input type="date">` and bypasses the form widget — the form is still used for server-side validation, and keeping its widget consistent avoids future drift if the template is ever changed to render the form directly.
- **New `formatacao-data` capability spec, mirroring `formatacao-monetaria`.** The existing money-formatting capability already documents the Brazilian display/input standard as its own spec, independent of any single Django app; date formatting deserves the same treatment since it's also a cross-cutting concern (it touches `lancamentos` forms and any future date field).

## Risks / Trade-offs

- [Risk] Native browser date pickers have inconsistent visuals across browsers (Chrome, Firefox, Safari render their own picker UI). → Mitigation: acceptable — the goal is a real calendar and correct format, not pixel-perfect cross-browser consistency, and this matches the existing "Pagar" field's behavior already in production.
- [Risk] If `format="%Y-%m-%d"` is omitted on any new DateField added later, the same "blank input on edit" bug could resurface. → Mitigation: document the pattern in the new `formatacao-data` spec so it's checked going forward.

## Migration Plan

No data migration. Pure widget/template-free code change in `lancamentos/forms.py`. Rollback is a plain revert.
