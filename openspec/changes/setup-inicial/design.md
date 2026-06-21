# Design — Implementação em Python/Django

> Decisões técnicas de implementação para o sistema de controle financeiro pessoal.
> Complementa `proposal.md` e as specs em `specs/` desta change. Este documento cobre
> o **como construir**, não o **o que construir**.

## Stack

- **Backend:** Python + Django.
- **Banco de dados:** SQLite para uso pessoal/familiar (baixo volume de escrita, sem
  concorrência pesada). Migrar para Postgres só se houver uso simultâneo frequente
  por múltiplas pessoas ou necessidade de relatórios mais pesados.
- **Frontend:** Django templates + HTMX, em vez de SPA. As interações do mockup
  (ações inline como Pagar/Editar/Excluir, filtros de status) não justificam manter
  uma API separada e um frontend desacoplado desde o início.
- **Deploy:** Docker, no mesmo NAS que já hospeda outros serviços do usuário — mais
  um serviço no `docker-compose` existente.

## Apps Django (mapeadas às capabilities do spec)

As fronteiras de domínio definidas em `specs/` mapeiam quase 1:1 para apps Django,
o que mantém a separação de responsabilidades clara desde o início:

| App             | Responsabilidade                                              |
|------------------|----------------------------------------------------------------|
| `contas`         | Cadastro de contas (Cartão, Banco, Investimento) e seus campos |
| `lancamentos`     | Entradas/saídas, tipos, cálculo de status                      |
| `parcelas`       | Geração de lançamentos de compra parcelada                     |
| `meses`           | Criação de mês, propagação, saldo, pendências                  |
| `visualizacao`   | Visão de conta, Visão consolidada, visão de patrimônio, comparativo |

## Pontos de complexidade

A complexidade real do sistema não está no Django em si, está nas regras de
propagação/recorrência definidas no spec. Vale tratá-las com cuidado especial:

### Lógica de negócio em service layer, não em signals ou models gordos
A lógica de criação de mês, propagação e cascata de edição/exclusão de lançamentos
recorrentes deve viver em um service layer dedicado (ex.: `meses/services.py`),
não em `post_save` signals nem espalhada em métodos de model. Isso facilita testar
isoladamente as regras de cascata e deixa o fluxo explícito em code review.

### Vínculo entre instâncias de um lançamento recorrente
Para implementar "editar afeta meses futuros" e "excluir remove instâncias
futuras", é necessário um vínculo de dados entre as cópias de um mesmo lançamento
recorrente ao longo dos meses. Sugestão: campo `grupo_recorrencia` (FK
auto-referenciada para o lançamento "origem", ou um modelo `SerieRecorrente`
separado que cada instância referencia).

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
  controlar quais meses já foram "criados" pelo usuário.
- **Contas Investimento:** saldo acumulado tratado separadamente do saldo
  consolidado de Banco/Cartão; não deve ser somado nas mesmas queries de saldo do
  mês corrente.

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

- **API (Django REST Framework):** não necessária nesta change, mas a separação
  entre service layer e views facilita adicionar uma API depois, caso surja
  interesse em um app mobile complementar.
