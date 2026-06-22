## 1. Enforce month-opening sequence rules

- [ ] 1.1 Add service-layer validation in `meses/services.py` to allow only current month as first opened month
- [ ] 1.2 Add service-layer validation in `meses/services.py` to allow only immediate next month after latest opened month
- [ ] 1.3 Keep idempotent behavior when `criar_mes` is called for an already opened month
- [ ] 1.4 Return clear validation message containing the allowed month (`MM/AAAA`) when sequence is violated

## 2. Make parcelas purchase-flow only

- [ ] 2.1 Remove `PARCELA_CARTAO` propagation branch from month-opening logic in `meses/services.py`
- [ ] 2.2 Ensure month propagation still covers fixed recurring types (`RECEBIMENTO_FIXO`, `GASTO_FIXO`, `ASSINATURA`)
- [ ] 2.3 Keep installment generation centralized in `parcelas/services.py` purchase flow

## 3. Align lancamento recurrence semantics

- [ ] 3.1 Remove `PARCELA_CARTAO` from recurring classification (`TIPOS_PROPAGAVEIS`) in `lancamentos/models.py`
- [ ] 3.2 Verify recurring edit cascade (`atualizar_serie_futura`) no longer applies series-wide updates to parcelas
- [ ] 3.3 Verify recurring delete cascade (`excluir_serie_futura`) no longer removes parcelas as recurring series

## 4. Update month-opening feedback in visualization

- [ ] 4.1 Handle month-opening validation errors in `visualizacao/views.py` and surface user-facing feedback
- [ ] 4.2 Update `templates/visualizacao/mes_nao_criado.html` to show the allowed month and actionable next step
- [ ] 4.3 Ensure consolidated flow keeps navigation coherent when month creation is rejected by sequence rules

## 5. Expand and adapt tests

- [ ] 5.1 Add tests in `meses/tests.py` for first month must be current month
- [ ] 5.2 Add tests in `meses/tests.py` for strict no-skip sequence and immediate-next success case
- [ ] 5.3 Add regression test proving month opening does not create duplicate parcelas after purchase generation
- [ ] 5.4 Update affected tests in `visualizacao/tests.py` for sequence-validation feedback behavior
- [ ] 5.5 Refactor date-sensitive tests to be deterministic under current-month-first rule

## 6. Update specs and docs

- [ ] 6.1 Validate spec deltas for `meses`, `parcelas`, `lancamentos`, and `visualizacao` with `openspec validate`
- [ ] 6.2 Align wording in project docs with canonical parcela ownership and sequential month-opening rule
- [ ] 6.3 Update `README.md` as the final step of execution to reflect the new behavior and correct OpenSpec command examples
