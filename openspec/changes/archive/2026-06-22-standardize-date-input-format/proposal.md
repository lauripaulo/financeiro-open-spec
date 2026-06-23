## Why

Date input fields across the app are inconsistent: the inline "Pagar" field on the consolidated view already uses a native `type="date"` input (showing the dd/mm/yyyy format with a calendar picker, per the browser's pt-BR locale), but the date fields on the lancamento creation/edit forms and the compra-parcelada form are plain Django `DateField` widgets, which render as free-text inputs with no calendar and no format guidance. Users have to type the date manually and can get the format wrong.

## What Changes

- All date entry fields (`Data de vencimento` on the lancamento form, `Data da compra` on the compra-parcelada form) switch to the native HTML5 `type="date"` widget, matching the pattern already used for "Data de pagamento" in the Pagar action.
- Since `LANGUAGE_CODE = 'pt-br'` is already configured, the browser renders these inputs with the dd/mm/yyyy format and its built-in calendar picker automatically — no new JS library needed.
- Widgets explicitly set `format="%Y-%m-%d"` so the value attribute stays ISO-8601 (required by `type="date"`) regardless of Django's locale-aware formatting, while the user-facing display remains dd/mm/yyyy via the browser.
- No change to read-only date displays (tables already use the `|date:"d/m/Y"` filter, already in the Brazilian format).

## Capabilities

### New Capabilities
- `formatacao-data`: defines the display and input-mask standard for all dates in the system (dd/mm/yyyy display, native calendar picker on entry), mirroring the existing `formatacao-monetaria` capability for money fields.

### Modified Capabilities
(none — this introduces a new cross-cutting formatting capability rather than changing an existing one's requirements)

## Impact

- Forms: `lancamentos/forms.py` (`LancamentoForm.Meta.widgets["data_vencimento"]`, `CompraParceladaForm.data_compra`, `MarcarPagoForm.data_pagamento`).
- Templates: `templates/lancamentos/form.html`, `templates/lancamentos/form_edicao.html`, `templates/lancamentos/form_compra_parcelada.html` (all render via `{{ form.as_p }}`, so no template changes needed beyond the widget).
- No database/model changes; no new dependencies.
