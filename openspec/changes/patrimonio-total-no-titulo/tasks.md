## 1. Calculo do total de patrimonio na view

- [x] 1.1 Atualizar `visualizacao/views.py` para calcular `total_patrimonio` somando os saldos acumulados das contas de investimento
- [x] 1.2 Garantir que `total_patrimonio` seja `Decimal("0.00")` quando nao houver contas de investimento
- [x] 1.3 Enviar `total_patrimonio` no contexto do template de `visao_patrimonio`

## 2. Exibicao do total no titulo da tela

- [x] 2.1 Atualizar `templates/visualizacao/patrimonio.html` para renderizar o titulo no formato `Visao de patrimonio: Total {{ total_patrimonio|moeda }}`
- [x] 2.2 Preservar exibicao atual dos cards por conta e historico de movimentos sem alteracoes funcionais

## 3. Testes de comportamento

- [x] 3.1 Adicionar teste em `visualizacao/tests.py` validando titulo com total consolidado quando ha contas de investimento
- [x] 3.2 Adicionar teste em `visualizacao/tests.py` validando titulo com `R$ 0,00` quando nao ha contas de investimento
- [x] 3.3 Garantir que os testes existentes da Visao de patrimonio continuem passando

## 4. Verificacao final

- [x] 4.1 Executar `python manage.py test visualizacao` e registrar resultado
