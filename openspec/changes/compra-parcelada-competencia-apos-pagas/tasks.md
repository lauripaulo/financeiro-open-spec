## 1. Ajuste da logica de competencia e vencimento

- [x] 1.1 Atualizar `parcelas/services.py` para separar indice de numeracao (`parcela_atual`) e indice de calendario na geracao parcial
- [x] 1.2 Garantir que a primeira parcela restante sempre use o mes seguinte a `data_compra` para `competencia_ano/mes`
- [x] 1.3 Garantir que `data_vencimento` siga a mesma sequencia mensal de `competencia_ano/mes` sem saltos

## 2. Preservacao de regras existentes

- [x] 2.1 Manter descricao e `parcela_atual` no formato original `N/total` mesmo com competencia reiniciada no mes seguinte
- [x] 2.2 Manter o calculo de valor por parcela inalterado com base em `valor_total` e `total_parcelas` originais
- [x] 2.3 Confirmar que validacoes de `parcelas_pagas` permanecem intactas

## 3. Testes de regressao e comportamento esperado

- [x] 3.1 Atualizar teste de geracao parcial em `parcelas/tests.py` para validar `6/10` com competencia `07/2026` no exemplo de compra `25/06/2026` e `5` pagas
- [x] 3.2 Adicionar/ajustar assercoes para validar sequencia de competencias e vencimentos das parcelas restantes (`07/2026` a `11/2026`)
- [x] 3.3 Garantir que o caso sem parcelas pagas (10x completo) continua passando sem alteracao de comportamento

## 4. Verificacao final

- [x] 4.1 Executar `python manage.py test parcelas lancamentos` e registrar resultado
