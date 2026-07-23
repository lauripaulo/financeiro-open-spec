## Context

Coverage run today shows **97% statement coverage** (3837 statements, 104 missed). The misses are concentrated in defensive code paths, error branches, migration reverse functions, model helper branches, and a few view htmx/error handlers. Most apps are already above 90%, so the work is a final push rather than a large test rewrite.

## Goals / Non-Goals

**Goals:**
- Reach 100% statement coverage across all Python source files in the repo.
- Cover every currently missed line with a focused unit/integration test using Django's `TestCase`.
- Keep the existing test style: Portuguese domain language, inline fixtures, minimal mocks.
- Use `coverage run manage.py test` and `coverage report -m` as the verification command.

**Non-Goals:**
- No new business logic or spec-level behavior changes.
- No new dependencies beyond `coverage` (already installed).
- No chasing branch coverage beyond statement coverage.
- No rewriting tests solely to satisfy coverage metrics if the code is unreachable dead code.

## Decisions

### 1. Prefer tests over code deletion
For missed defensive branches that represent real failure modes (e.g., invalid decimal input, missing POST field, external URL rejection), add a test. Only delete code when it is provably unreachable.

### 2. Make htmx/error paths testable without browser automation
Views that return `HttpResponseBadRequest` or htmx 204 responses can be exercised with Django's test client and header injection (`HX-Request: true`). No Playwright or Selenium.

### 3. Keep migration coverage pragmatic
Migration reverse functions and no-op data-migration reverses are missed because tests normally run migrations forward only. We will add lightweight migration tests only where the migration contains custom Python logic (e.g., `flip_negative_to_positive`). Auto-generated no-op reverses may be left uncovered if they contain no project logic.

### 4. Extract or parametrize where a branch is hard to hit
If a private branch depends on external state that is hard to reproduce, prefer extracting a pure helper so it becomes unit-testable. Example: date-parsing utility functions in `visualizacao/views.py` that currently sit inside view functions.

## Risks / Trade-offs

- **Risk:** Some branches may require contrived inputs that do not reflect real usage. → Mitigation: if a branch is truly unreachable, delete it instead of testing it.
- **Risk:** Refactoring to add testability can introduce bugs. → Mitigation: make mechanical changes only; run the full suite after each app.
- **Risk:** Coverage may regress quickly. → Mitigation: the final task adds a CI/local pre-commit command so future changes are checked.
