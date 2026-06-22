## Why

The current domain behavior allows two writers for `PARCELA_CARTAO` (purchase flow and month opening), which can produce duplicate installments and ambiguous ownership of installment lifecycle. Month creation also allows opening arbitrary months, which breaks the intended temporal chain and introduces inconsistency in propagation and balances.

## What Changes

- Make `CompraParcelada` the single source of truth for generating `PARCELA_CARTAO` installments.
- Remove `PARCELA_CARTAO` generation from month opening propagation.
- Enforce month-opening sequence rules:
  - First opened month must be the current month.
  - After the first month, only the immediate next month can be opened (no skip).
- Keep idempotent behavior when requesting a month that is already open.
- Remove `PARCELA_CARTAO` from recurring cascade semantics used for recurring edit/delete flows.
- Improve user feedback for invalid month-opening attempts by showing the allowed month.
- Update docs and tests to reflect the canonical behavior, including README updates at the end of execution.

## Capabilities

### New Capabilities
- *(none)*

### Modified Capabilities
- `meses`: month opening becomes strictly sequential and no longer propagates `PARCELA_CARTAO`.
- `parcelas`: installment generation is explicitly owned by purchase flow only.
- `lancamentos`: `PARCELA_CARTAO` no longer participates in recurring-series cascade behavior.
- `visualizacao`: month-opening UI feedback now communicates the allowed month when sequence rules are violated.

## Impact

- Backend services in `meses/services.py` and purchase/installment behavior in `parcelas/services.py`.
- Recurrence classification in `lancamentos/models.py` and related edit/delete flows.
- Month-opening feedback flow in `visualizacao/views.py` and templates.
- OpenSpec spec deltas for `meses`, `parcelas`, `lancamentos`, and `visualizacao`.
- Test suite updates for sequential month constraints and parcela non-duplication.
