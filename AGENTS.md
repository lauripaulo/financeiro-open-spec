# Repository Guidelines

## How to Investigate
1. Read highest-value sources: `README.md`, root manifests, workspace config, lockfiles.
2. Check build/test/lint/typecheck/codegen configs and CI/pre-commit workflows.
3. Review existing instructions: `AGENTS.md`, `CLAUDE.md`, `.opencode/`.
4. Verify architecture by inspecting representative code (entrypoints, package boundaries).
5. Trust executable sources over prose.

## Project Structure & Module Organization
Django app with SQLite. Configuration in `financeiro/`.
- `contas/`: `Banco`, `Cartao`, `Investimento`
- `lancamentos/`: Entries, types, status, recurrence cascade
- `parcelas/`: Installment generation
- `meses/`: Month lifecycle (manual/sequential), balance chaining
- `visualizacao/`: Reports, filters
- `importacao/`: OFX Import (Nubank)
- `templates/`, `static/`, `openspec/`
- Logic resides in `services.py` for each app.

## Workflow & Tools
### OpenSpec (Source of Truth)
- `openspec/specs/`: Main specifications
- `openspec/changes/`: Active changes
- `openspec/changes/archive/`: Completed changes
- Commands: `openspec list --json`, `openspec validate --changes`, `openspec list --archived`

### Agent Commands
- `/opsx-explore`: Explore ideas/requirements
- `/opsx-propose`: Propose changes with artifacts
- `/opsx-apply`: Implement tasks
- `/opsx-sync`: Sync delta specs
- `/opsx-archive`: Archive changes

## Build, Test, and Development Commands
Local Environment:
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Docker (Dev):
```bash
docker compose up --build
```

Tests:
- All: `.venv/bin/python manage.py test`
- App-specific: `.venv/bin/python manage.py test <app_name>`

## Coding Style & Naming Conventions
- Standard Django: `models.py`, `forms.py`, `views.py`, `urls.py`, `services.py` (for logic).
- 4-space indentation, snake_case variables, PascalCase classes.
- Portuguese domain names: `Conta`, `Lancamento`, `Mes`, `Parcela`, `competencia_ano`, `competencia_mes`.

## Testing Guidelines
- Use `django.test.TestCase` in `tests.py`.
- Name classes after behavior (e.g., `ContaViewTests`).
- Add focused tests for model validation, service rules, and view responses.
- Use inline records or existing helpers.

## Commit & Pull Request Guidelines
- Conventional commits: `feat: ...`, `fix: ...`, `chore: ...`.
- PRs must describe behavior, mention OpenSpec changes, include test results, and screenshots for UI.

## Security & Configuration Tips
- No real financial data or local DB snapshots in commits.
- Keep secrets out of `financeiro/settings.py`.
- `db.sqlite3` is local artifact.
