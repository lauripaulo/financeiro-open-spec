# Design — improve-ux-forms-consolidada

## Decisoes (fechadas em entrevista)

1. **Largura em 2 camadas.** `.container` global `max-width: 1200px`; wrapper
   `.form-page` `max-width: 600px` nos forms. Alternativas rejeitadas: so forms
   estreitos (consolidada continuaria sem respiro); max-width unico (~900px)
   deixaria forms de coluna unica largos demais.
2. **Grid 2 colunas como padrao nos forms.** `descricao` e selects em span 2;
   datas/numeros/moeda em meia coluna. Escolha do usuario (recomendacao original
   era coluna unica com pares pontuais).
3. **Condicionais em JS vanilla declarativo.** `data-show-when="campo=V1|V2"`
   no wrapper `.m3-field`, script generico `conditional-fields.js`. Rejeitado
   HTMX re-render (round-trip por selecao) e forms separados por tipo
   (multiplica rotas). Regras sao estaticas e conhecidas no cliente;
   `clean()` continua fonte de verdade.
4. **Campo oculto = `disabled`.** Browser nao submete; `clean()` passa; valor
   preservado no DOM se o usuario reverter a selecao antes de salvar. Rejeitado
   limpar valor (perda de dado digitado) e deixar server rejeitar (erro em campo
   invisivel).
5. **Tipo dirige conta no lancamento.** Filtragem unidirecional; opcao
   incompativel selecionada e limpa. Rejeitada filtragem bidirecional (risco de
   deadlock de UX).
6. **`lancamento_vinculado` fora do form.** Vinculo e detalhe interno do fluxo
   de transferencia. Edicao manual poderia quebrar concordancia do par.
7. **Consolidada: totais como stat-cards no topo**; barra unica de navegacao +
   filtros. Rejeitado layout 2 colunas (apertaria a tabela — restricao firme de
   legibilidade).
8. **Pendentes e Ajustar saldo colapsaveis (`<details>`), fechados por padrao**,
   com contador + badge no summary de pendentes quando > 0.
9. **Pagar em popover** com data pre-preenchida (hoje). Mantem o mesmo POST
   HTMX `marcar_pago`. Sem lib nova.
10. **Desktop-only.** Sem trabalho responsivo alem do que o grid der.

## Mapa de condicionais

| Contexto | Selecao | Mostra | Esconde (disabled) |
|---|---|---|---|
| ContaForm | tipo=CARTAO | dia_vencimento | saldo_atual, limite_negativo |
| ContaForm | tipo=BANCO | saldo_atual, limite_negativo | dia_vencimento |
| ContaForm | tipo=INVESTIMENTO | saldo_atual | dia_vencimento, limite_negativo |
| LancamentoForm | tipo=APORTE/RESGATE | contas Investimento | demais contas |
| LancamentoForm | demais tipos | contas Banco/Cartao | contas Investimento |

Filtragem de conta requer `data-conta-tipo` em cada `<option>` (widget `Select`
custom com `create_option` em `lancamentos/forms.py`).

## Glossario (novo CONTEXT.md)

- **Lancamento vinculado** — par interno criado pelo fluxo de transferencia; nao
  e conceito editavel pelo usuario.
- **Pagar** — marcar lancamento como pago com data explicita; status e computado,
  nunca armazenado.
- **Pendentes do mes anterior** — lancamentos nao pagos do mes fechado
  aguardando decisao transferir/manter.
