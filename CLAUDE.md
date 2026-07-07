# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Run migrations + dev server
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver

# Tests
.venv/bin/python manage.py test                # all
.venv/bin/python manage.py test lancamentos    # single app

# Docker
docker compose up --build
```

OpenSpec CLI (for spec management):
```bash
openspec list --json
openspec validate --changes
openspec list --archived
```

## Architecture

Django project with SQLite. The `financeiro/` directory holds project config (settings, root urls). Domain logic is split across five apps:

| App | Responsibility |
|---|---|
| `contas` | Account types: `Banco`, `Cartao`, `Investimento` |
| `lancamentos` | Financial entries, 9 types, status, recurrence cascade |
| `parcelas` | Installment purchase generation (only source of `PARCELA_CARTAO`) |
| `meses` | Month lifecycle: sequential opening, propagation, balance chain |
| `visualizacao` | Reporting views, template filters, consolidated views |

Templates live in `templates/`, static assets in `static/`. Frontend uses Django templates + HTMX with Material Design 3.

### Service Layer

Complex business logic lives in `services.py` inside each app — never in signals or fat models. Key services:

- `meses/services.py` — `criar_mes()` enforces sequential month opening (only the next month after the last opened can be created), propagates recurrent entries (`RECEBIMENTO_FIXO`, `GASTO_FIXO`, `ASSINATURA`), and chains `saldo_inicial` by (conta, mês).
- `parcelas/services.py` — `gerar_parcelas_da_compra()` is the **only** place `PARCELA_CARTAO` entries are created. Month opening never creates them.

### Key Domain Rules

- **Status is computed** via `Lancamento.status` property and `LancamentoQuerySet` methods (`.pagos()`, `.pendentes()`, `.previstos()`). No stored field, no cron job.
- **Recurrence chain** — `grupo_recorrencia` is a self-FK on `Lancamento` pointing to the origin instance. Editing/deleting a recurrent entry cascades to future months. `PARCELA_CARTAO` never participates in this cascade.
- **Monetary values** always use `DecimalField`, never `FloatField`.
- **`Conta.Investimento`** balance is tracked separately and excluded from `Banco`/`Cartao` consolidated queries.
- **`lancamento_vinculado`** is a bidirectional self-FK for paired entries (e.g., transfer pairs). Sync is done with `queryset.update()` to avoid recursive `full_clean()` calls.

### OpenSpec Workflow

Change proposals and specs live in `openspec/`. Active changes are under `openspec/changes/`, main specs under `openspec/specs/`, archived changes under `openspec/changes/archive/`. Claude Code skills `/opsx-propose`, `/opsx-apply`, `/opsx-sync`, `/opsx-archive` orchestrate the spec-driven workflow.

## Naming Conventions

Domain terminology is Portuguese. Keep new concepts consistent: `Conta`, `Lancamento`, `Mes`, `Parcela`, `competencia_ano`, `competencia_mes`, `grupo_recorrencia`. File layout follows standard Django: `models.py`, `forms.py`, `views.py`, `urls.py`, `services.py`, `tests.py`, `admin.py`. 4-space indentation, snake_case for functions/variables, PascalCase for classes.

## Tests

Tests use `django.test.TestCase`, live in each app's `tests.py`. Prioritize coverage for: recurrence propagation, cascade edit/delete on future months, chained balance calculation, and sequential month validation. Create minimal records inline or with existing helper functions in the test module.
