## Context

The current implementation allows two different writers for `PARCELA_CARTAO`: the purchase flow in `parcelas/services.py` and month opening propagation in `meses/services.py`. This creates ambiguity about ownership of installment lifecycle and can produce duplicate installments for the same month.

Month opening also accepts arbitrary target months, which allows users to skip months and break the intended temporal chain for propagation and balance handling. The change must preserve existing stack choices (Django + service layer) and apply prospectively from current data state, without retroactive backfill.

## Goals / Non-Goals

**Goals:**
- Establish a single source of truth for `PARCELA_CARTAO` generation.
- Enforce strict month-opening sequence: first month must be current month, then immediate next month only.
- Keep month opening idempotent for already-open months.
- Remove installment types from recurring-series cascade behavior.
- Improve UX feedback when users attempt to open an invalid month.
- Align specs, tests, and README with the canonical behavior.

**Non-Goals:**
- Retroactively repairing historical gaps in existing `MesAberto` records.
- Reworking the overall domain model into new entities for installment series.
- Changing deployment architecture or introducing new external dependencies.

## Decisions

1. **Single writer for parcelas**
   - Decision: only purchase flow generates `PARCELA_CARTAO` installments.
   - Rationale: avoids double-write behavior and duplicate installment risk.
   - Alternatives considered:
     - Keep dual writers and deduplicate by heuristics: rejected due to fragile rules and hidden coupling.
     - Move to month-opening-only materialization: rejected due to larger behavioral change and weaker future visibility.

2. **Strict sequential month opening**
   - Decision: enforce allowed target month in `criar_mes`.
     - No opened month yet: only current month is valid.
     - Existing months: only immediate next month after latest open month is valid.
   - Rationale: preserves temporal consistency and prevents skipped-month chain breaks.
   - Alternatives considered:
     - Allow arbitrary future month and infer missing months: rejected due to hidden side effects and uncertain saldo propagation.
     - Hard-stop system if historical gaps exist: rejected per product decision to enforce prospectively.

3. **Prospective enforcement from current state**
   - Decision: continue forward from latest opened month, without auto-fixing historical gaps.
   - Rationale: lowest risk rollout with predictable behavior and no data migration burden.
   - Alternatives considered:
     - Backfill all gaps automatically: rejected due to migration complexity and possible unintended propagated data.

4. **Parcela excluded from recurring cascade semantics**
   - Decision: remove `PARCELA_CARTAO` from recurring classification used by bulk edit/delete recurrence logic.
   - Rationale: installment lifecycle is schedule-based from purchase, not recurring-template propagation.
   - Alternatives considered:
     - Keep cascade behavior for parcelas: rejected because it conflicts with single-writer ownership model.

5. **Explicit UI feedback for invalid month creation attempts**
   - Decision: when sequence rule fails, surface the allowed month (`MM/AAAA`) in user-facing feedback.
   - Rationale: makes strict rule understandable and actionable.
   - Alternatives considered:
     - Generic validation error only: rejected because it increases user confusion.

## Risks / Trade-offs

- [Risk] Existing tests that open arbitrary historical months may fail under new rule. -> Mitigation: update tests to create month chains relative to current date and/or controlled date fixtures.
- [Risk] Users accustomed to opening any month will see stricter validation. -> Mitigation: show clear allowed-month guidance and preserve idempotent open behavior.
- [Trade-off] Legacy gaps remain in historical data. -> Mitigation: enforce deterministic behavior prospectively from latest open month.

## Migration Plan

1. Implement service-layer month-sequence guard and explicit validation messaging.
2. Remove `PARCELA_CARTAO` from month propagation path.
3. Remove `PARCELA_CARTAO` from recurring cascade classification.
4. Update visualizacao feedback paths/templates for invalid month-open attempts.
5. Update OpenSpec deltas and README to document canonical behavior.
6. Run and adjust tests for sequence enforcement and parcela non-duplication.

Rollback strategy: revert code changes for sequence guard and parcela propagation in a single rollback commit if regressions are detected.

## Open Questions

- Should the month-opening error feedback always redirect to the allowed month, or keep user on requested month with actionable create button for the allowed month?
- Should admin-level tools remain free to create non-sequential months for maintenance, or follow the same service-layer guard universally?
