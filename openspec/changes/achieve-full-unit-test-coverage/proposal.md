## Why

The project currently has 97% unit test coverage, with 104 uncovered statements spread across models, forms, views, services, migrations and management helpers. The remaining gaps are mostly defensive branches, error paths and edge cases that can hide regressions in critical financial logic. Closing these gaps gives the team confidence to refactor and ship changes safely.

## What Changes

- Audit the current coverage report and classify every uncovered line by app and risk.
- Add missing unit tests for the uncovered statements in `contas`, `lancamentos`, `meses`, `parcelas`, `visualizacao`, `importacao` and project-level files.
- Refactor only where necessary to make code testable (e.g., extracting pure helpers, adding seams for mocking, removing dead branches).
- Keep the existing test style and conventions (Django `TestCase`, Portuguese domain language, inline fixtures).
- Reach and maintain **100% statement coverage** across the Python codebase.

## Capabilities

### New Capabilities
- `cobertura-testes-unitarios`: establishes the goal and verification mechanism for 100% unit test coverage, including per-app coverage gates.

### Modified Capabilities
- None. This change does not alter spec-level requirements; it only adds tests and minimal testability refactors.

## Impact

- Test files in every app (`*/tests.py`).
- Small refactors in `contas/models.py`, `lancamentos/views.py`, `meses/services.py`, `parcelas/models.py`, `visualizacao/views.py` and other modules to make untested branches reachable or remove dead code.
- Coverage configuration remains in `manage.py` workflow; no new build pipeline.
- CI/local verification command: `.venv/bin/coverage run manage.py test && .venv/bin/coverage report -m`.
