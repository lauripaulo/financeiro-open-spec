# financeiro-open-spec

Repositorio de especificacao com OpenSpec para um sistema de controle financeiro pessoal.

Este repo contem os artefatos OpenSpec e a implementacao inicial em Django.

## Escopo 

- Cadastro de contas: `Cartao`, `Banco`, `Investimento`
- Lancamentos com 9 tipos, direcao (entrada/saida) e propagacao por tipo
- Status calculado automaticamente: `Previsto`, `Pendente`, `Pago`
- Parcelas de cartao geradas exclusivamente pelo fluxo de compra parcelada
- Criacao manual de mes com sequencia obrigatoria (primeiro mes = mes atual; cada proximo mes = imediatamente seguinte)
- Propagacao de recorrentes fixos (`RECEBIMENTO_FIXO`, `GASTO_FIXO`, `ASSINATURA`) na abertura de mes
- Cascata de edicao/exclusao para recorrentes em meses futuros (exceto `PARCELA_CARTAO`)
- Visoes: por conta, consolidada (Banco + Cartao), patrimonio (Investimento) e comparativo

## Stack alvo (planejada)

- Backend: Python + Django
- Banco: SQLite
- Frontend: Django templates + HTMX
- Deploy: Docker

## Como executar (rapido)

### Opcao 1: ambiente local

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Acesse: `http://127.0.0.1:8000/`

### Opcao 2: Docker Compose

```bash
docker compose up --build
```

Acesse: `http://127.0.0.1:8000/`

### Testes

```bash
.venv/bin/python manage.py test
```

## Comandos OpenSpec uteis

```bash
openspec list --json
openspec validate --changes
openspec validate enforce-sequential-month-opening-and-parcela-source
openspec list --archived
```

## Atalhos de comando para sessoes OpenCode

Este repo inclui comandos em `.opencode/commands/`:

- `/opsx-explore`
- `/opsx-propose`
- `/opsx-apply`
- `/opsx-sync`
- `/opsx-archive`
