## 1. Form widgets

- [x] 1.1 Add `"data_vencimento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")` to `LancamentoForm.Meta.widgets` in `lancamentos/forms.py`
- [x] 1.2 Set the same `DateInput` widget on `CompraParceladaForm.data_compra` in `lancamentos/forms.py`
- [x] 1.3 Set the same `DateInput` widget on `MarcarPagoForm.data_pagamento` in `lancamentos/forms.py` (for consistency, even though the current template hand-writes the input)
- [x] 1.4 Ensure `input_formats` accepts `"%Y-%m-%d"` for all three fields (Django's default `DATE_INPUT_FORMATS` already includes ISO, so this should require no extra change — verify only)

## 2. Verification

- [x] 2.1 Run `python manage.py test` and confirm all existing tests still pass
- [x] 2.2 Manually verify in the dev server: "Novo lancamento" form's Data de vencimento field shows the native calendar picker and dd/mm/yyyy display
- [x] 2.3 Manually verify: editing an existing lancamento pre-fills the Data de vencimento field correctly (no blank date bug)
- [x] 2.4 Manually verify: "Nova compra parcelada" form's Data da compra field shows the native calendar picker and dd/mm/yyyy display
