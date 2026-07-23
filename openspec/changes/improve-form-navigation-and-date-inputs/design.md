## Context

A UI atual já usa templates Django com classes Material Design 3 e campos condicionais via JavaScript leve. A avaliação em produção mostrou que os formulários principais têm apenas ação primária (`Salvar`, `Transferir`, `Gerar parcelas`, `Importar`), sem uma ação explícita para cancelar ou voltar, e que seletores mês/ano aparecem como campos numéricos separados em telas de consulta.

Campos de data reais já estão majoritariamente corretos (`type="date"`) em lançamentos, compra parcelada, transferência, pagamento e planejamento. O problema restante é transformar essa regra em contrato verificável e separar data real de competência mensal.

## Goals / Non-Goals

**Goals:**

- Padronizar ações secundárias em formulários sem duplicar HTML em cada template.
- Preservar o contexto de origem da Visão consolidada ao salvar ou cancelar fluxos iniciados nela.
- Manter todos os campos de data real como controles nativos de calendário.
- Usar um controle único de competência mensal para filtros mês/ano onde isso melhora a leitura.
- Evitar que `limite_negativo` seja preenchido com valor negativo novamente.

**Non-Goals:**

- Introduzir datepicker customizado, framework JS ou pipeline de build.
- Redesenhar toda a navegação principal.
- Alterar regras de domínio de saldo, status, recorrência ou importação OFX.
- Modificar o Django Admin.

## Decisions

### 1. Usar partial de ações de formulário

Criar um partial reutilizável para a barra final do formulário, por exemplo `_partials/form_actions.html`, recebendo `primary_label`, `secondary_label` e `secondary_url`.

Alternativa considerada: repetir links `Cancelar`/`Voltar` manualmente em cada template. Rejeitada porque perpetua inconsistência e torna fácil esquecer novos formulários.

### 2. `Cancelar` vs `Voltar` depende do risco de perda de dados

Usar `Cancelar` em criação/edição com dados não salvos: conta, lançamento, edição de lançamento, compra parcelada e transferência. Usar `Voltar` em fluxos operacionais ou sem edição persistente em andamento, como importação OFX antes do envio ou telas de resultado.

Alternativa considerada: sempre usar `Voltar`. Rejeitada porque em formulários editáveis o termo não comunica que alterações serão descartadas.

### 3. URL de retorno explícita e segura

Views que abrem formulários a partir da Visão consolidada devem carregar um `return_url` com os filtros de origem (`ano`, `mes`, `conta`, `status`, `pagina` quando aplicável). O cancelamento e o redirect pós-sucesso devem usar essa URL quando for local; caso contrário, cair para fallback explícito da tela.

Alternativa considerada: depender apenas de `HTTP_REFERER`. Rejeitada porque é instável, pode estar ausente e não deve controlar navegação sem validação.

### 4. Distinguir data real de competência mensal

Campos que representam um dia específico continuam com `input type="date"`. Filtros que representam mês/ano devem usar controle de competência mensal, preferencialmente `input type="month"`, mantendo parse e fallback server-side para `ano`/`mes` quando necessário.

Alternativa considerada: manter dois `number` inputs para mês e ano. Rejeitada para telas principais porque permite combinações visualmente frágeis e exige mais interação do usuário.

### 5. Validar `limite_negativo` como valor positivo

O formulário/modelo de Conta deve deixar claro que `limite_negativo` é informado como magnitude positiva (`2000,00`, não `-2000,00`) e rejeitar valor negativo. Isso evita falso alerta de limite, pois a regra interna calcula o limite real como `-limite_negativo`.

Alternativa considerada: apenas adicionar help text. Rejeitada porque o erro já ocorreu em produção e helper sozinho não impede recorrência.

## Risks / Trade-offs

- `input type="month"` pode variar entre navegadores → manter parse server-side tolerante e fallback visual aceitável.
- Preservar `return_url` pode abrir risco de redirect externo → validar URL local antes de redirecionar.
- Partial genérico pode esconder contexto específico → manter labels explícitos por template (`Salvar`, `Salvar alteracoes`, `Transferir`, `Gerar parcelas`, `Importar`).
- Validação positiva de `limite_negativo` pode rejeitar dados legados negativos → orientar correção manual/migração simples antes de editar conta.

## Migration Plan

- Adicionar partial de ações e aplicá-lo aos formulários de usuário.
- Adicionar construção/validação de `return_url` nas views afetadas.
- Trocar controles mês/ano das consultas para competência mensal onde aplicável, preservando compatibilidade com URLs `ano`/`mes` existentes.
- Adicionar helper e validação para `limite_negativo` positivo.
- Cobrir com testes de template/view e rodar `.venv/bin/python manage.py test`.
