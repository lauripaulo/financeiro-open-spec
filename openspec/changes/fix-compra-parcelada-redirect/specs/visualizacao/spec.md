## ADDED Requirements

### Requirement: Retorno ao mes de origem apos registrar lancamento ou compra parcelada
O sistema SHALL retornar o usuario para a Visao consolidada do mes que estava sendo
visualizado quando o formulario de "Novo lancamento" ou "Nova compra parcelada" foi
aberto, apos o registro ser concluido com sucesso. Esse mes de origem SHALL ser
preservado mesmo quando a data de vencimento, a data da compra ou o mes da primeira
parcela gerada forem diferentes do mes de origem.

#### Scenario: Registro de lancamento retorna ao mes de origem
- GIVEN o usuario esta na Visao consolidada de julho/2026
- WHEN ele clica em "Novo lancamento", preenche o formulario e salva
- THEN o sistema SHALL retornar a Visao consolidada de julho/2026

#### Scenario: Registro de compra parcelada retorna ao mes de origem
- GIVEN o usuario esta na Visao consolidada de julho/2026
- WHEN ele clica em "Nova compra parcelada", preenche o formulario com uma data de
  compra de marco/2026 e clica em "Gerar parcelas"
- THEN o sistema SHALL gerar as parcelas normalmente
- AND SHALL retornar a Visao consolidada de julho/2026, nao a de marco/2026 nem a do
  mes da primeira parcela gerada
