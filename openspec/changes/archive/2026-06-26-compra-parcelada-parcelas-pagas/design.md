## Context

O fluxo atual de compra parcelada recebe descricao, valor total, total de parcelas, conta cartao e data da compra, e sempre gera toda a serie de parcelas no momento do cadastro. O caso de uso alvo e migracao de controle vindo de planilha, em que o usuario ja pagou parte da compra fora do sistema e deseja registrar somente as parcelas futuras.

O dominio ja persiste `total_parcelas` e `parcela_atual` em cada lancamento de parcela, o que permite manter numeracao original da serie mesmo gerando um subconjunto. Nao ha necessidade de nova persistencia para `parcelas_pagas` nesta iteracao.

## Goals / Non-Goals

**Goals:**
- Permitir informar `parcelas_pagas` no cadastro de compra parcelada com default `0`.
- Validar no backend a faixa permitida e impedir cadastro sem parcelas a gerar.
- Gerar apenas parcelas restantes, mantendo numeracao `N/total` e metadados (`parcela_atual`, `total_parcelas`) da serie original.
- Preservar regra atual de vencimento ancorada em `data_compra`.
- Melhorar UX do formulario com limite dinamico e ajuste automatico de `parcelas_pagas` quando `total_parcelas` diminuir.

**Non-Goals:**
- Persistir `parcelas_pagas` no modelo `CompraParcelada`.
- Criar historico retroativo de parcelas ja pagas.
- Alterar regras de propagacao entre meses ou de pagamento de fatura.

## Decisions

1. `parcelas_pagas` sera um campo de formulario (nao de modelo) com `min=0` e validacao cruzada com `total_parcelas`.
   - Rationale: atende o requisito com menor impacto de schema e sem migracao.
   - Alternative considered: adicionar coluna em `CompraParcelada`; descartado por nao agregar valor imediato ao fluxo acordado.

2. A geracao continuara calculando os valores de parcela com base em `valor_total/total_parcelas` originais e gerara apenas indices de `parcelas_pagas + 1` ate `total_parcelas`.
   - Rationale: preserva consistencia financeira e numeracao original da serie.
   - Alternative considered: recalcular cada parcela com base no saldo restante; descartado por perder correspondencia com a compra original.

3. O calendario de vencimentos permanecera ancorado na `data_compra` (primeira parcela no mes seguinte da compra), mesmo quando `parcelas_pagas > 0`.
   - Rationale: mantem regra de dominio atual e previsibilidade de implementacao.
   - Alternative considered: deslocar vencimentos pelo numero de parcelas pagas; descartado por decisao explicita do usuario no grilling.

4. O frontend ajustara dinamicamente o `max` de `parcelas_pagas` conforme `total_parcelas` e fara clamp automatico quando necessario, mantendo validacao server-side como fonte de verdade.
   - Rationale: reduz erros de preenchimento sem abrir mao de integridade.

## Risks / Trade-offs

- [Risco] Compra antiga com `parcelas_pagas > 0` pode gerar lancamentos com vencimento no passado devido ancora em `data_compra` -> Mitigacao: comportamento documentado e validado com o usuario; sem ajuste automatico de datas nesta iteracao.
- [Risco] Sem persistir `parcelas_pagas`, auditoria posterior nao mostra explicitamente quantas parcelas ja estavam pagas no momento do cadastro -> Mitigacao: manter numeracao `N/total` nos lancamentos criados e reavaliar persistencia em iteracao futura se virar necessidade.
- [Trade-off] Acrescentar JS no template aumenta acoplamento de UX a logica de formulario -> Mitigacao: manter script pequeno e defensivo; backend continua garantindo regras criticas.
