# financeiro-open-spec

Repositorio de especificacao com OpenSpec para um sistema de controle financeiro pessoal.

Este repo descreve o produto (regras, design e tarefas).

## Escopo 

- Cadastro de contas: `Cartao`, `Banco`, `Investimento`
- Lancamentos com 9 tipos, direcao (entrada/saida) e propagacao por tipo
- Status calculado automaticamente: `Previsto`, `Pendente`, `Pago`
- Parcelas de cartao com geracao automatica por mes
- Criacao manual de mes com propagacao de recorrentes e tratamento de pendencias
- Cascata de edicao/exclusao para recorrentes em meses futuros
- Visoes: por conta, consolidada (Banco + Cartao), patrimonio (Investimento) e comparativo

## Stack alvo (planejada)

- Backend: Python + Django
- Banco: SQLite
- Frontend: Django templates + HTMX
- Deploy: Docker

## Comandos OpenSpec uteis

```bash
openspec list --json
openspec status --change "setup-inicial"
openspec validate setup-inicial
```

## Atalhos de comando para sessoes OpenCode

Este repo inclui comandos em `.opencode/commands/`:

- `/opsx-explore`
- `/opsx-propose`
- `/opsx-apply`
- `/opsx-sync`
- `/opsx-archive`
