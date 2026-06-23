## Why

Submitting a new `Lancamento` can currently crash with `RelatedObjectDoesNotExist` instead of returning form validation errors. This happens when model validation dereferences `self.conta` before the relation is guaranteed to be present, creating a 500 in a normal invalid-input path.

## What Changes

- Harden `Lancamento` model validation so account-dependent rules never dereference a missing relation.
- Ensure invalid submissions (for example, account/type incompatibility) are surfaced as field errors in the form, not server exceptions.
- Add regression tests that reproduce the current failure path and verify the request returns a normal invalid form response.
- Keep existing business rules intact (APORTE/RESGATE account restrictions, investment-account restrictions, parcela/cartao restrictions), changing only validation robustness and error delivery.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `lancamentos`: strengthen validation behavior so invalid create/edit submissions always return user-facing validation errors and SHALL NOT crash due to missing related `conta` during model clean.

## Impact

- Affected app: `lancamentos` (model validation, form/view regression tests).
- No schema/database migration.
- No API contract change; user-facing impact is improved error handling stability on invalid form submissions.
