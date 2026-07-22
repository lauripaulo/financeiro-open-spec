# Repository Guidelines

## Core Architecture Rules
- **Business Logic**: MUST live in `services.py` of each app. NEVER in `models.py` or signals.
- **Domain Language**: Portuguese (`Conta`, `Lancamento`, `Mes`, `Parcela`, `competencia_ano`, `competencia_mes`).
- **Code Style**: 4-space indentation, `snake_case` variables, `PascalCase` classes.

## Module Responsibilities
- `contas/`: `Banco`, `Cartao`, `Investimento` (Investimento has separate balance).
- `lancamentos/`: Entries, types, status (Previsto, Pendente, Pago - calculated, not persisted), recurrence cascade.
- `parcelas/`: `PARCELA_CARTAO` generated ONLY via card purchase flow.
- `meses/`: Month lifecycle, sequential opening, balance chaining (`saldo_inicial`).
- `visualizacao/`: Reports, filters, and template-side views.
- `importacao/`: OFX Import (Nubank) with deduplication by `FITID`.

## OpenSpec Workflow (Source of Truth)
- `openspec/specs/`: Main specifications.
- `openspec/changes/`: Active changes.
- `openspec/changes/archive/`: Completed changes.
- **Commands**: 
  - `openspec list --json`
  - `openspec validate --changes`
  - `openspec list --archived`
- **Agent Skills**: `/opsx-explore`, `/opsx-propose`, `/opsx-apply`, `/opsx-sync`, `/opsx-archive`.

## Development & Deployment
### Local Environment
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

### Docker
- **Dev**: `docker compose up --build`
- **Production/NAS**: `docker compose -f docker-compose.nas.yml up -d --build`

### Testing
- **All**: `.venv/bin/python manage.py test`
- **App-specific**: `.venv/bin/python manage.py test <app_name>`

## Security & Ops
- **No secrets**: Keep secrets out of `financeiro/settings.py`.
- **No real data**: Never commit real financial data or `db.sqlite3` snapshots.
- **Commits**: Use Conventional Commits (`feat:`, `fix:`, `chore:`).
- **PRs**: Must include behavior description, OpenSpec change references, test results, and UI screenshots.
