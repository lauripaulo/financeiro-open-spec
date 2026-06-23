## Context

`Lancamento.clean()` currently reads `self.conta.tipo` in multiple branches. During `ModelForm` validation, if the `conta` field fails to bind cleanly (or is excluded after field-level errors), Django still calls model `clean()`, and dereferencing `self.conta` can raise `RelatedObjectDoesNotExist`. That turns an expected invalid-form response into a 500 error in `criar_lancamento`.

The business rules themselves are correct and should remain unchanged:
- APORTE/RESGATE only for investment accounts.
- Investment accounts accept only APORTE/RESGATE/automatic CONCILIACAO.
- PARCELA_CARTAO requires card account.

## Goals / Non-Goals

**Goals:**
- Ensure `Lancamento` validation is robust when `conta` relation is missing during model cleaning.
- Return standard form validation errors (HTTP 200 with form errors) instead of unhandled exceptions.
- Add regression coverage for the failing path and preserve existing domain constraints.

**Non-Goals:**
- No changes to accounting semantics or allowed type/account combinations.
- No database schema change or data migration.
- No UI redesign of form error presentation.

## Decisions

- Guard account-dependent checks in `Lancamento.clean()` behind an explicit account-presence check (`conta_id` / safely resolved `conta`) before reading `conta.tipo`.
  - Rationale: the model layer must tolerate partial instances during form validation.
  - Alternative considered: move all account-type rules to `LancamentoForm.clean()`. Rejected because model-level invariants should remain enforced for non-form entry points.

- Keep current validation messages and field attribution where possible (`conta`/`tipo`) and only change control flow to avoid crashes.
  - Rationale: minimizes user-facing behavior changes and keeps compatibility with existing tests and UX expectations.
  - Alternative considered: simplify to one generic non-field error. Rejected due to reduced usability.

- Add regression tests at both form and view level for the invalid APORTE + non-investment account submission path.
  - Rationale: this is the observed production failure path and ensures no future regression in end-to-end form handling.
  - Alternative considered: model-only test. Rejected because the failure manifests during `form.is_valid()` in the view.

## Risks / Trade-offs

- [Risk] Over-guarding could accidentally skip valid rule checks when account is present. -> Mitigation: structure logic as "if account missing, emit account error; else run existing type/account rules unchanged" and cover with regression tests.
- [Risk] Multiple validation layers (form + model) can duplicate messages. -> Mitigation: keep checks coherent and assert only key user-visible errors in tests, not fragile exact ordering.

## Migration Plan

No migration required. Deploy as application-code change only. Rollback is a direct revert of the validation guard and tests.

## Open Questions

None.
