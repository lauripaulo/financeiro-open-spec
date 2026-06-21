## Why

Uma auditoria entre a implementacao atual e os documentos `proposta.md` e `arquitetura.md` mostrou lacunas funcionais importantes no fluxo principal (cadastro de contas para usuario final, tratamento de pendentes na criacao de mes e consistencia da visao por conta), alem de algumas divergencias de implementacao que podem gerar comportamento inconsistente.
Corrigir essas lacunas agora reduz retrabalho, evita ambiguidade nas regras de negocio e deixa o sistema pronto para evolucao com base nas especificacoes oficiais.

## What Changes

- Adicionar fluxo de cadastro de contas para usuario final (fora do admin), incluindo criacao, edicao e exclusao com as validacoes de dominio existentes.
- Ajustar a criacao de mes para explicitar a decisao sobre pendentes como parte do fluxo de abertura do novo mes, com validacao de elegibilidade para transferencia.
- Fortalecer a Visao de conta com comportamento consistente de totais e saldo quando um filtro de conta estiver ativo.
- Restringir criacao manual de lancamentos para impedir inconsistencias com `Parcela de Cartao`, mantendo compra parcelada como caminho oficial para gerar parcelas.
- Alinhar consultas de status e pendencia com o padrao de QuerySet da arquitetura e ampliar cobertura de testes para os cenarios de borda identificados.

## Capabilities

### New Capabilities
- *(none)*

### Modified Capabilities
- `contas`: incluir requisitos de cadastro de contas para usuario final no fluxo principal da aplicacao.
- `visualizacao`: ajustar requisitos da visao por conta para garantir consistencia de saldo/totais e separar claramente a visao consolidada.
- `meses`: refinar requisitos de tratamento de pendentes durante abertura de mes e regras de transferencia.
- `lancamentos`: adicionar requisitos para validacoes de criacao manual de tipos especiais e consistencia de filtros por status.

## Impact

- Backend Django: `contas`, `lancamentos`, `meses`, `visualizacao`, `parcelas`.
- Templates HTMX: novas telas/acoes de contas e ajustes em consolidada/fluxo de criacao de mes.
- Services e QuerySets: consolidacao de regras de status/pendencia e validacoes de transferencia.
- Testes: ampliacao de suite de servicos e views para cobrir os gaps de comportamento encontrados na auditoria.
