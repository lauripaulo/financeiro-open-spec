# financeiro-open-spec

Sistema de controle financeiro pessoal em Django, desenvolvido com workflow spec-driven usando [OpenSpec](https://github.com/Fission-AI/OpenSpec).

## Funcionalidades

- **Contas**: cadastro de `Banco`, `Cartao` e `Investimento` (investimento tem saldo proprio, fora das visoes consolidadas)
- **Lancamentos**: 9 tipos, direcao entrada/saida, status calculado automaticamente (`Previsto`, `Pendente`, `Pago`) — sem campo persistido nem cron
- **Meses**: abertura manual e sequencial (primeiro mes = mes atual; cada proximo = imediatamente seguinte), com encadeamento de `saldo_inicial` por conta
- **Recorrencia**: `RECEBIMENTO_FIXO`, `GASTO_FIXO` e `ASSINATURA` propagam na abertura de mes; edicao/exclusao cascateia para meses futuros
- **Parcelas**: compras parceladas de cartao geram `PARCELA_CARTAO` exclusivamente pelo fluxo de compra parcelada (nunca pela abertura de mes, nunca em cascata de recorrencia)
- **Transferencias**: pares de lancamentos vinculados (`lancamento_vinculado`) sincronizados entre contas
- **Importacao OFX**: extrato de conta corrente e fatura de cartao Nubank, com deduplicacao por FITID
- **Visoes**: por conta, consolidada (Banco + Cartao), patrimonio (Investimento) e comparativo

## Stack

- Python 3.12 + Django 5.2
- SQLite
- Django templates + HTMX, Material Design 3
- Gunicorn + WhiteNoise (producao), Docker

## Estrutura

| App | Responsabilidade |
|---|---|
| `contas` | Tipos de conta: `Banco`, `Cartao`, `Investimento` |
| `lancamentos` | Lancamentos, tipos, status, cascata de recorrencia |
| `parcelas` | Geracao de parcelas de compra no cartao |
| `meses` | Ciclo de vida do mes: abertura sequencial, propagacao, saldo encadeado |
| `visualizacao` | Visoes, relatorios e filtros de template |
| `importacao` | Importacao de arquivos OFX (Nubank) |

Regra de arquitetura: logica de negocio vive em `services.py` de cada app — nunca em signals ou models gordos. Configuracao do projeto em `financeiro/`, templates em `templates/`, estaticos em `static/`.

## Como executar

### Ambiente local

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Acesse: `http://127.0.0.1:8000/`

### Docker (desenvolvimento)

```bash
docker compose up --build
```

Acesse: `http://127.0.0.1:8000/`

### Docker (producao / NAS)

```bash
cp .env.example .env    # preencha DJANGO_SECRET_KEY e DJANGO_ALLOWED_HOSTS
mkdir -p data           # banco SQLite persiste em ./data/db.sqlite3
docker compose -f docker-compose.nas.yml up -d --build
```

Acesse: `http://<ip-do-servidor>:8231/`

Variaveis de ambiente (ver `.env.example`):

| Variavel | Obrigatoria | Descricao |
|---|---|---|
| `DJANGO_SECRET_KEY` | sim | Gere com `python3 -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DJANGO_ALLOWED_HOSTS` | sim | IPs/hostnames de acesso, separados por virgula |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | se https ou porta custom | Origens com esquema, ex: `http://192.168.1.10:8231` |
| `GUNICORN_WORKERS` | nao | Padrao: 2 |

O container roda `migrate` e `collectstatic` automaticamente no boot.

### Testes

```bash
.venv/bin/python manage.py test                # todos
.venv/bin/python manage.py test lancamentos   # um app
```

## Workflow OpenSpec

Propostas de mudanca e especificacoes vivem em `openspec/`:

- `openspec/specs/` — especificacoes principais (fonte de verdade)
- `openspec/changes/` — mudancas ativas
- `openspec/changes/archive/` — mudancas concluidas

Comandos uteis:

```bash
openspec list --json
openspec validate --changes
openspec list --archived
```

Skills/comandos para sessoes com agentes (Claude Code em `.claude/`, OpenCode em `.opencode/commands/`):

- `/opsx-explore` — explorar ideias e requisitos
- `/opsx-propose` — propor mudanca com artefatos completos
- `/opsx-apply` — implementar tarefas de uma mudanca
- `/opsx-sync` — sincronizar delta specs com specs principais
- `/opsx-archive` — arquivar mudanca concluida

## Licenca

Ver [LICENSE](LICENSE).
