# Repository Guidelines

## Project Structure & Module Organization

This is a Django personal finance application backed by SQLite. The Django project configuration lives in `financeiro/`. Domain apps are split by responsibility: `contas/` for accounts, `lancamentos/` for financial entries, `parcelas/` for installment behavior, `meses/` for month lifecycle rules, and `visualizacao/` for reporting views and template filters. Shared HTML templates live in `templates/`, static browser assets in `static/`, and OpenSpec change/spec documents in `openspec/`. Keep migrations inside each app's `migrations/` directory.

## Build, Test, and Development Commands

Create and install a local environment:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Run database migrations and start the development server:

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Run the app with Docker:

```bash
docker compose up --build
```

Run tests with Django's test runner:

```bash
.venv/bin/python manage.py test
```

Useful OpenSpec checks:

```bash
openspec list --json
openspec validate --changes
openspec list --archived
```

## Coding Style & Naming Conventions

Follow standard Django structure: models in `models.py`, forms in `forms.py`, view logic in `views.py`, URL routing in `urls.py`, and domain operations in `services.py` when behavior spans models or views. Use 4-space indentation, descriptive snake_case for functions and variables, and PascalCase for classes. Existing domain names are Portuguese; keep new user-facing labels and domain concepts consistent with terms like `Conta`, `Lancamento`, `Mes`, `Parcela`, `competencia_ano`, and `competencia_mes`.

## Testing Guidelines

Tests use `django.test.TestCase` and live in each app's `tests.py`. Name test classes after the behavior under test, for example `ContaViewTests`, and methods with `test_...`. Add focused tests for model validation, service rules, and view responses whenever behavior changes. Prefer creating minimal records inline or with small helper functions already present in test modules.

## Commit & Pull Request Guidelines

Git history mostly uses short conventional-style commits such as `feat: ...`, `fix: ...`, and `chore: ...`; keep new commits imperative and scoped. Pull requests should describe the behavior change, mention related OpenSpec changes or issues, include test results from `manage.py test`, and attach screenshots for template or UI changes.

## Security & Configuration Tips

Do not commit real financial data or local database snapshots. Treat `db.sqlite3` and backup copies as local development artifacts. Keep production secrets out of `financeiro/settings.py`; the current settings are development-oriented with `DEBUG = True` and SQLite defaults.
