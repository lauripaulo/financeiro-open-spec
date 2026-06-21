# Tasks

## 1. Setup do projeto
- [x] 1.1 Criar projeto Django e configurar settings (apps, timezone, locale pt-br)
- [x] 1.2 Configurar banco de dados (SQLite) e Dockerfile/docker-compose para deploy

## 2. App `contas`
- [x] 2.1 Modelo de Conta com tipos (Cartão, Banco, Investimento) e campos específicos
- [x] 2.2 Validação de saldo inicial obrigatório (Banco/Investimento)
- [x] 2.3 Regra de exclusão bloqueada quando há lançamentos associados
- [x] 2.4 Alerta de limite negativo em conta Banco (sem bloqueio)
- [x] 2.5 Testes de modelo e regras de negócio

## 3. App `lancamentos`
- [x] 3.1 Modelo de Lançamento com Tipo e Status calculado (property + QuerySet customizado)
- [x] 3.2 Implementar os 9 tipos de lançamento e suas regras de direção/propagação
- [x] 3.3 Restringir Conciliação a criação automática (não manual)
- [x] 3.4 Restringir Aporte/Resgate a contas Investimento
- [x] 3.5 Testes de cálculo de status (Previsto/Pendente/Pago)

## 4. App `parcelas`
- [x] 4.1 Geração automática de N lançamentos Parcela de Cartão a partir de uma compra
- [x] 4.2 Vencimento de cada parcela seguindo o dia configurado na conta Cartão
- [x] 4.3 Descrição automática com progresso (`1/10`, `2/10`, ...)
- [x] 4.4 Testes de geração de parcelas

## 5. App `meses`
- [x] 5.1 Modelo de controle de meses criados (ex.: `MesAberto`)
- [x] 5.2 Service layer de criação de mês com propagação por tipo
- [x] 5.3 Vínculo de série recorrente (`grupo_recorrencia`) entre instâncias propagadas
- [x] 5.4 Cascata de edição (sobrescreve customização futura) e exclusão (remove
      instâncias futuras) de lançamentos recorrentes
- [x] 5.5 Tratamento de lançamentos pendentes do mês anterior na criação do novo mês
- [x] 5.6 Cálculo de saldo encadeado (saldo_inicial armazenado por conta/mês) e
      geração automática de Conciliação
- [x] 5.7 Aviso ao ultrapassar o limite de 12 meses futuros (sem bloqueio)
- [x] 5.8 Testes de propagação, cascata e cálculo de saldo

## 6. App `visualizacao`
- [x] 6.1 Visão de conta
- [x] 6.2 Visão consolidada (Banco + Cartão)
- [x] 6.3 Visão de patrimonio (Investimento)
- [x] 6.4 Navegação entre meses (seletor + anterior/próximo)
- [x] 6.5 Confirmação ao editar mês encerrado
- [x] 6.6 Comparativo entre meses (padrão: atual vs. anterior)
- [x] 6.7 Ações inline (Pagar/Editar/Excluir) via HTMX

## 7. Admin e finalização
- [x] 7.1 Configurar Django Admin para contas/lançamentos
- [x] 7.2 Revisão geral e `openspec validate setup-inicial`
- [x] 7.3 `openspec archive setup-inicial` ao concluir
