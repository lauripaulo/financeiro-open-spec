## 1. Formulario e validacoes de compra parcelada

- [x] 1.1 Atualizar `CompraParceladaForm` em `lancamentos/forms.py` para incluir `parcelas_pagas` com `min_value=0`, `initial=0` e validacao cruzada com `total_parcelas`
- [x] 1.2 Bloquear submissao quando `parcelas_pagas == total_parcelas`, exibindo erro de validacao e sem criar registros
- [x] 1.3 Garantir que o `save()` do formulario repasse `parcelas_pagas` para o servico de geracao

## 2. Geracao de parcelas restantes

- [x] 2.1 Ajustar `gerar_parcelas_da_compra` em `parcelas/services.py` para aceitar `parcelas_pagas` e gerar somente de `parcela_atual = parcelas_pagas + 1` ate `total_parcelas`
- [x] 2.2 Preservar calculo de valor por parcela baseado na serie original (`valor_total` e `total_parcelas`) e manter descricao no formato `N/total`
- [x] 2.3 Manter vencimentos ancorados na `data_compra` original ao filtrar parcelas geradas

## 3. UX do formulario na tela Nova compra parcelada

- [x] 3.1 Renderizar o campo `parcelas_pagas` no formulario com valor inicial `0`
- [x] 3.2 Adicionar script no template `templates/lancamentos/form_compra_parcelada.html` para sincronizar `max` de `parcelas_pagas` com `total_parcelas`
- [x] 3.3 Implementar ajuste automatico de `parcelas_pagas` quando `total_parcelas` diminuir abaixo do valor atual

## 4. Testes e verificacao

- [x] 4.1 Atualizar/adicionar testes em `parcelas/tests.py` para cobrir geracao parcial (ex.: 10x com 3 pagas gera 4/10..10/10)
- [x] 4.2 Adicionar teste para rejeicao quando `parcelas_pagas == total_parcelas` sem criacao de compra/lancamentos
- [x] 4.3 Adicionar teste de validacao de faixa (`parcelas_pagas < 0` e `parcelas_pagas > total_parcelas`)
- [x] 4.4 Executar suite de testes alvo (`python manage.py test parcelas lancamentos`) e registrar resultado
