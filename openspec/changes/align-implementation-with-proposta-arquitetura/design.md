## Context

A base atual em Django/HTMX cobre boa parte das regras do dominio, mas a auditoria recente encontrou lacunas entre a implementacao real e os documentos `proposta.md` e `arquitetura.md`. Os principais pontos sao: ausencia de fluxo de contas para usuario final, inconsistencias na visao por conta (filtro de lista e total consolidado nao seguem o mesmo escopo), e tratamento de pendentes fora do momento de abertura do mes.

O objetivo desta mudanca e fechar esses gaps sem alterar o stack nem o desenho principal de apps. A correcao deve preservar o service layer em `meses/services.py` e manter a experiencia principal em templates + HTMX.

## Goals / Non-Goals

**Goals:**
- Entregar CRUD de contas no fluxo principal da aplicacao (nao apenas admin), respeitando validacoes de dominio ja existentes.
- Ajustar o fluxo de abertura de mes para incorporar decisao de pendentes como etapa do processo.
- Garantir consistencia de dados na Visao de conta: lista, totais e saldo no mesmo escopo.
- Evitar criacao manual inconsistente de `PARCELA_CARTAO` e manter compra parcelada como caminho oficial para parcelas.
- Alinhar o uso de filtros de status entre listagem e calculo de saldo, com cobertura de testes adicional.

**Non-Goals:**
- Criar API REST ou alterar o modelo de deploy.
- Reescrever o frontend para SPA.
- Introduzir novos tipos de conta ou novos tipos de lancamento.
- Alterar regras de negocio fora dos gaps identificados na auditoria.

## Decisions

1. **Adicionar app-flow de contas com views dedicadas e formularios tipados**
   - **Decisao:** criar rotas/templates de contas no fluxo principal com acoes de criar, editar e excluir.
   - **Racional:** elimina dependencia do admin para operacao diaria e atende requisito funcional de iniciar uso pelo cadastro de conta.
   - **Alternativas consideradas:**
     - Usar apenas Django Admin: rejeitada por nao atender o fluxo do usuario final descrito na proposta.
     - Criar uma tela unica de cadastro sem edicao/exclusao: rejeitada por cobertura incompleta.

2. **Formalizar abertura de mes em duas fases (criar base + resolver pendentes)**
   - **Decisao:** manter criacao manual, mas exigir resolucao explicita de pendentes do mes anterior antes de concluir a abertura para uso normal.
   - **Racional:** alinha comportamento com regra funcional "ao criar o novo mes, decidir cada pendente".
   - **Alternativas consideradas:**
     - Manter pendentes apenas como bloco informativo apos abertura: rejeitada por continuar desalinhada com spec.
     - Transferir todos automaticamente: rejeitada por remover decisao do usuario.

3. **Separar escopo de saldo consolidado vs saldo de conta filtrada**
   - **Decisao:** quando `conta` estiver selecionada, calcular totais/saldo somente para essa conta; quando nao houver filtro, manter consolidado Banco+Cartao.
   - **Racional:** evita discrepancia entre linhas exibidas e saldo mostrado.
   - **Alternativas consideradas:**
     - Manter sempre saldo consolidado e apenas filtrar linhas: rejeitada por confundir a leitura da visao de conta.

4. **Restringir criacao manual de tipos especiais**
   - **Decisao:** remover `PARCELA_CARTAO` do formulario manual de lancamento (assim como `CONCILIACAO`) e manter `compra parcelada` como fluxo unico para parcelas.
   - **Racional:** impede erros de validacao por campos de parcela ausentes e reforca origem correta dos dados.
   - **Alternativas consideradas:**
     - Permitir `PARCELA_CARTAO` manual com novos campos no form: rejeitada por duplicar fluxo e aumentar risco de inconsistencias de serie.

5. **Padronizar filtros de status via QuerySet para listagem e regras de pendencia**
   - **Decisao:** usar os metodos de `LancamentoQuerySet` como fonte comum para filtros de status e pendentes.
   - **Racional:** reduz divergencia entre regras de listagem, saldo e identificacao de pendentes.
   - **Alternativas consideradas:**
     - Manter filtragem em Python apos materializar queryset: rejeitada por risco de comportamento divergente e pior eficiencia.

## Risks / Trade-offs

- **[Risco]** Mudanca no fluxo de abertura de mes pode quebrar navegacao atual de HTMX. **-> Mitigacao:** introduzir passo intermediario com testes de view e manter fallback de redirecionamento claro.
- **[Risco]** Ajuste de saldo por conta filtrada pode alterar expectativa de usuarios acostumados com saldo sempre consolidado. **-> Mitigacao:** rotular explicitamente o tipo de saldo exibido na UI.
- **[Trade-off]** Mais telas de contas aumentam manutencao de templates. **-> Mitigacao:** reutilizar componentes simples de formulario e mensagens.
- **[Trade-off]** Validacoes mais estritas de transferencia de pendentes podem recusar operacoes antes aceitas. **-> Mitigacao:** retornar mensagem objetiva explicando criterio de elegibilidade.

## Migration Plan

1. Introduzir rotas/views/templates de contas e publicar navegacao para acesso no layout principal.
2. Ajustar services e views de meses/visualizacao para fluxo de pendentes durante abertura.
3. Atualizar calculo de totais/saldo com escopo por conta quando filtro estiver ativo.
4. Restringir formulario manual de lancamento para evitar `PARCELA_CARTAO`.
5. Expandir testes de servicos e views para cobrir novos cenarios.
6. Deploy sem migracao destrutiva de dados; rollback por revert de codigo caso necessario.

## Open Questions

- A confirmacao de pendentes na abertura do mes deve bloquear totalmente a tela principal ate todas as decisoes, ou permitir salvar parcial e retomar?
- Na visao com conta filtrada, o texto deve mudar para "Saldo da conta" para evitar ambiguidade com "Saldo consolidado"?
