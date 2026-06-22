# Design — Implementação em Python/Django

> Decisões técnicas de implementação para o sistema de controle financeiro pessoal.
> Complementa `project.md` e as specs funcionais em `specs/`. Este documento cobre o
> **como construir**, não o **o que construir**.

## Stack

- **Backend:** Python + Django.
- **Banco de dados:** SQLite para uso pessoal/familiar (baixo volume de escrita, sem
  concorrência pesada). Migrar para Postgres só se houver uso simultâneo frequente
  por múltiplas pessoas ou necessidade de relatórios mais pesados.
- **Frontend:** Django templates + HTMX, em vez de SPA. As interações do mockup
  (ações inline como Pagar/Editar/Excluir, filtros de status) não justificam manter
  uma API separada e um frontend desacoplado desde o início.
- **Deploy:** Docker, no mesmo NAS que já hospeda Immich e Nextcloud — mais um
  serviço no `docker-compose` existente.

## Apps Django (mapeadas às capabilities do spec)

As fronteiras de domínio definidas em `specs/` mapeiam quase 1:1 para apps Django,
o que mantém a separação de responsabilidades clara desde o início:

| App             | Responsabilidade                                              |
|------------------|----------------------------------------------------------------|
| `contas`         | Cadastro de contas (Cartão, Banco, Investimento) e seus campos |
| `lancamentos`     | Entradas/saídas, tipos, cálculo de status                      |
| `parcelas`       | Geração de lançamentos de compra parcelada                     |
| `meses`           | Criação de mês, propagação, saldo, pendências                  |
| `visualizacao`   | Visão de conta, Visão consolidada, comparativo, histórico       |

## Pontos de complexidade

A complexidade real do sistema não está no Django em si, está nas regras de
propagação/recorrência definidas no spec. Vale tratá-las com cuidado especial:

### Lógica de negócio em service layer, não em signals ou models gordos
A lógica de criação de mês, propagação e cascata de edição/exclusão de lançamentos
recorrentes deve viver em um service layer dedicado (ex.: `meses/services.py`),
não em `post_save` signals nem espalhada em métodos de model. Isso facilita testar
isoladamente as regras de cascata (edição sobrescreve customização futura, exclusão
remove instâncias futuras já criadas) e deixa o fluxo explícito em code review.

### Abertura de mês estritamente sequencial
A criação de mês (`criar_mes`) aplica uma guarda de sequência obrigatória:
- Se não existe nenhum mês aberto, apenas o mês/ano atual pode ser o primeiro.
- Se já existem meses abertos, apenas o mês imediatamente seguinte ao último
  mês aberto pode ser criado (sem pular).
- Chamadas para um mês já aberto são idempotentes — retornam o mês existente
  sem erro.
A validação está centralizada em `_validar_sequencia_mes` dentro de
`meses/services.py` e levanta `ValidationError` com o mês permitido no formato
`MM/AAAA` sempre que a regra for violada.

### Fonte única de verdade para Parcela de Cartão
Lançamentos do tipo `PARCELA_CARTAO` são gerados **exclusivamente** pelo fluxo de
compra parcelada em `parcelas/services.py` (`gerar_parcelas_da_compra`). A
abertura de mês **não** propaga nem cria parcelas. Essa separação evita escrita
dupla e risco de duplicação de parcelas.

### Vínculo entre instâncias de um lançamento recorrente
Para implementar "editar afeta meses futuros" e "excluir remove instâncias
futuras", é necessário um vínculo de dados entre as cópias de um mesmo lançamento
recorrente ao longo dos meses. Sugestão: campo `grupo_recorrencia` (FK
auto-referenciada para o lançamento "origem", ou um modelo `SerieRecorrente`
separado que cada instância referencia).

`PARCELA_CARTAO` **não** participa dessa cascata de recorrência — o ciclo de vida
de uma parcela é de agenda de compra, não de template recorrente propagado.
Os tipos recorrentes (propagados na abertura de mês e elegíveis para cascata de
edição/exclusão) são: `RECEBIMENTO_FIXO`, `GASTO_FIXO` e `ASSINATURA`.

### Saldo encadeado entre meses
Em vez de recalcular recursivamente o saldo desde o primeiro mês cadastrado toda
vez que um mês é aberto, armazenar explicitamente o `saldo_inicial` por
(conta, mês) no momento da criação do mês. A Conciliação só ajusta a partir
desse ponto, sem precisar revisitar o histórico completo.

### Status calculado, sem job/cron
Status (Previsto/Pendente/Pago) não precisa de campo armazenado nem de tarefa
agendada para transição. Resolver com:
- Property no model para exibição (`Lancamento.status`).
- `QuerySet` customizado para filtros/listagens, ex.:
  `Lancamento.objects.pendentes()` usando
  `Q(data_pagamento__isnull=True, data_vencimento__lt=hoje)`.

## Modelagem de dados

- **Valores monetários:** sempre `DecimalField`, nunca `FloatField`.
- **Controle de meses criados:** modelo explícito (ex.: `MesAberto(mes, ano)`) para
  controlar quais meses já foram "criados" pelo usuário — é uma regra de negócio
  própria, independente de existir lançamento ou não naquele mês.
- **Contas Investimento:** saldo acumulado tratado separadamente do saldo
  consolidado de Banco/Cartão (ver spec de `contas`); não deve ser somado nas
  mesmas queries de saldo do mês corrente.

## Frontend / Admin

- **Django Admin:** cobre boa parte da manutenção de baixo nível (cadastro de
  contas, correção pontual de lançamentos) sem esforço extra de UI.
- **Telas customizadas (HTMX):** reservadas para as views que o usuário realmente
  usa no dia a dia — Visão consolidada, comparativo entre meses, ação de Pagar
  inline sem reload de página.

## Testes

Dado que as regras de cascata de recorrência são a parte mais arriscada de
acertar (e a mais cara de corrigir depois de haver dados reais), priorizar
cobertura de testes em:
- Propagação de cada tipo de lançamento ao criar um novo mês.
- Edição de lançamento recorrente sobrescrevendo instância futura customizada.
- Exclusão de lançamento recorrente removendo instâncias futuras já criadas.
- Cálculo de saldo encadeado entre meses, incluindo ajuste de Conciliação.

## Evoluções futuras

- **API (Django REST Framework):** não necessária no MVP, mas a separação entre
  service layer e views facilita adicionar uma API depois, caso surja interesse
  em um app mobile complementar (ex.: registrar gastos direto do celular).