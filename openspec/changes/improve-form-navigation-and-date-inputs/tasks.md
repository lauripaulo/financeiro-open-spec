## 1. Form Actions

- [x] 1.1 Create reusable `_partials/form_actions.html` that renders primary submit and secondary navigation actions with M3 classes.
- [x] 1.2 Apply the partial to `contas/form.html`, `lancamentos/form.html`, `lancamentos/form_edicao.html`, `lancamentos/form_compra_parcelada.html`, `lancamentos/form_transferencia.html`, and `importacao/ofx_form.html`.
- [x] 1.3 Use `Cancelar` on create/edit forms and `Voltar` on operational import flows.
- [x] 1.4 Ensure secondary actions are links or buttons that do not submit the form.

## 2. Return Context

- [x] 2.1 Add safe local `return_url` handling for forms opened from the Visão consolidada, with explicit fallback URLs.
- [x] 2.2 Preserve `ano`, `mes`, `conta`, `status`, and `pagina` where applicable when generating links to create/edit flows.
- [x] 2.3 Redirect successful create/edit/transfer/compra parcelada submissions back to the safe return URL when present.
- [x] 2.4 Make `Cancelar` return to the same safe URL without submitting form data.

## 3. Date and Competência Inputs

- [x] 3.1 Audit all real date fields and keep them rendered as `input type="date"`.
- [x] 3.2 Replace month/year number pairs in Visão consolidada and Comparativo with a single competência mensal control (`type="month"` or equivalent).
- [x] 3.3 Parse competência mensal in views and keep compatibility with existing `ano`/`mes` query parameters.
- [x] 3.4 Keep month previous/next navigation in Visão consolidada unchanged.

## 4. Conta Limit Guidance

- [x] 4.1 Add help text to `limite_negativo` explaining that the value must be positive (example: `2000,00` for limit `-2000,00`).
- [x] 4.2 Add server-side validation rejecting negative `limite_negativo` values.
- [x] 4.3 Add tests covering negative rejection and positive acceptance.

## 5. Verification

- [x] 5.1 Add template/view tests asserting `Cancelar` or `Voltar` appears on each affected form.
- [x] 5.2 Add tests asserting real date fields render `type="date"` and competência controls render as month controls or equivalent.
- [x] 5.3 Add tests for safe return URL behavior, including rejection of external return URLs.
- [x] 5.4 Run `.venv/bin/python manage.py test`.
- [x] 5.5 Run `openspec validate --changes`.
