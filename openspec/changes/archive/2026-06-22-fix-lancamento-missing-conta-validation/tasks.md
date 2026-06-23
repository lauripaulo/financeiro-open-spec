## 1. Harden model validation flow

- [x] 1.1 Update `Lancamento.clean()` to guard account-dependent checks so `self.conta.tipo` is never dereferenced when `conta` is absent during validation
- [x] 1.2 Preserve current business validation rules and field-level error targets (`conta`/`tipo`) for APORTE, RESGATE, investimento-only constraints, and PARCELA_CARTAO checks

## 2. Add regression coverage

- [x] 2.1 Add a form-level regression test proving invalid APORTE + non-investment account returns validation errors without raising `RelatedObjectDoesNotExist`
- [x] 2.2 Add a view-level regression test for `criar_lancamento` POST confirming invalid input re-renders form with 200 instead of 500

## 3. Verify behavior end-to-end

- [x] 3.1 Run `python manage.py test lancamentos` and confirm all lancamentos tests pass
- [x] 3.2 Manually submit `/lancamentos/novo/` with incompatible account/type and confirm the page shows validation errors instead of Django debug exception
