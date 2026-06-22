## Contexto

A implementacao atual permite dois escritores para `PARCELA_CARTAO`: o fluxo de compra em `parcelas/services.py` e a propagacao na abertura de mes em `meses/services.py`. Isso gera ambiguidade sobre quem e responsavel pelo ciclo de vida das parcelas e pode produzir parcelas duplicadas para o mesmo mes.

A abertura de mes tambem aceita meses-alvo arbitrarios, o que permite pular meses e quebrar a cadeia temporal esperada para propagacao e saldo. Esta mudanca deve preservar as escolhas atuais de stack (Django + service layer) e aplicar as novas regras de forma prospectiva a partir do estado atual dos dados, sem backfill retroativo.

## Objetivos / Nao objetivos

**Objetivos:**
- Estabelecer uma fonte unica de verdade para geracao de `PARCELA_CARTAO`.
- Aplicar sequencia estrita na abertura de mes: primeiro mes deve ser o atual e depois apenas o mes imediatamente seguinte.
- Manter abertura de mes idempotente para meses ja abertos.
- Remover tipos de parcela da semantica de cascata de serie recorrente.
- Melhorar feedback de UX quando o usuario tentar abrir um mes invalido.
- Alinhar specs, testes e README com o comportamento canonico.

**Nao objetivos:**
- Reparar retroativamente lacunas historicas em `MesAberto`.
- Refatorar todo o modelo de dominio para novas entidades de serie de parcelas.
- Alterar arquitetura de deploy ou introduzir novas dependencias externas.

## Decisoes

1. **Fonte unica para parcelas**
   - Decisao: apenas o fluxo de compra gera parcelas `PARCELA_CARTAO`.
   - Racional: evita comportamento de escrita dupla e risco de duplicacao de parcelas.
   - Alternativas consideradas:
     - Manter dois escritores e deduplicar por heuristica: rejeitado por regras frageis e acoplamento oculto.
     - Gerar parcelas apenas na abertura de mes: rejeitado por ampliar a mudanca comportamental e reduzir previsibilidade futura.

2. **Abertura de mes estritamente sequencial**
   - Decisao: validar mes permitido em `criar_mes`.
     - Sem mes aberto: apenas o mes atual e valido.
     - Com meses abertos: apenas o mes imediatamente seguinte ao ultimo mes aberto e valido.
   - Racional: preserva consistencia temporal e impede quebra de cadeia por salto de mes.
   - Alternativas consideradas:
     - Permitir mes futuro arbitrario e inferir meses faltantes: rejeitado por efeitos colaterais ocultos e incerteza no saldo.
     - Bloquear o sistema quando houver lacunas historicas: rejeitado pela decisao de aplicar mudanca de forma prospectiva.

3. **Aplicacao prospectiva a partir do estado atual**
   - Decisao: seguir em frente a partir do ultimo mes aberto, sem correcao automatica de lacunas antigas.
   - Racional: rollout de menor risco, com comportamento previsivel e sem custo de migracao de dados.
   - Alternativas consideradas:
     - Preencher automaticamente todas as lacunas: rejeitado por complexidade de migracao e risco de dados propagados indevidos.

4. **Parcela fora da cascata de recorrencia**
   - Decisao: remover `PARCELA_CARTAO` da classificacao de recorrencia usada na logica de editar/excluir em massa.
   - Racional: ciclo de vida da parcela e de agenda de compra, nao de template recorrente propagado.
   - Alternativas consideradas:
     - Manter cascata para parcelas: rejeitado por conflitar com o modelo de fonte unica.

5. **Feedback explicito na UI para tentativa invalida de abertura**
   - Decisao: quando a regra de sequencia falhar, mostrar o mes permitido (`MM/AAAA`) para o usuario.
   - Racional: torna a regra estrita clara e acionavel.
   - Alternativas consideradas:
     - Exibir apenas erro generico de validacao: rejeitado por aumentar confusao do usuario.

## Riscos / Trade-offs

- [Risco] Testes existentes que abrem meses historicos arbitrarios podem falhar com a nova regra. -> Mitigacao: atualizar testes para criar cadeias de mes relativas a data atual e/ou com fixtures de data controlada.
- [Risco] Usuarios acostumados a abrir qualquer mes passarao a receber validacao estrita. -> Mitigacao: exibir orientacao clara do mes permitido e manter comportamento idempotente para mes ja aberto.
- [Trade-off] Lacunas historicas permanecem nos dados antigos. -> Mitigacao: comportamento deterministico aplicado prospectivamente a partir do ultimo mes aberto.

## Plano de migracao

1. Implementar guarda de sequencia de mes no service layer com mensagens explicitas de validacao.
2. Remover `PARCELA_CARTAO` da propagacao na abertura de mes.
3. Remover `PARCELA_CARTAO` da classificacao de cascata de recorrencia.
4. Atualizar fluxos/templates de feedback em `visualizacao` para tentativas invalidas de abertura de mes.
5. Atualizar deltas OpenSpec e README para documentar o comportamento canonico.
6. Rodar e ajustar testes para regra de sequencia e nao duplicacao de parcelas.

Estrategia de rollback: reverter, em um unico commit, as alteracoes de guarda de sequencia e propagacao de parcelas caso regressao seja detectada.

## Perguntas abertas com respostas

- O feedback de erro de abertura de mes deve sempre redirecionar para o mes permitido, ou manter o usuario no mes solicitado com acao para abrir o mes permitido?
  - manter o usuario no mes solicitado, com acao para abrir o mes permitido.
- Ferramentas de administracao devem continuar podendo criar meses fora da sequencia para manutencao, ou seguir universalmente a mesma guarda do service layer?
  - seguir universalmente a mesma guarda do service layer.
