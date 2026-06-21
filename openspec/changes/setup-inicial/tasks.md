# Tasks

## 1. Setup do projeto
- [ ] 1.1 Criar projeto Django e configurar settings (apps, timezone, locale pt-br)
- [ ] 1.2 Configurar banco de dados (SQLite) e Dockerfile/docker-compose para deploy

## 2. App `contas`
- [ ] 2.1 Modelo de Conta com tipos (Cartão, Banco, Investimento) e campos específicos
- [ ] 2.2 Validação de saldo inicial obrigatório (Banco/Investimento)
- [ ] 2.3 Regra de exclusão bloqueada quando há lançamentos associados
- [ ] 2.4 Alerta de limite negativo em conta Banco (sem bloqueio)
- [ ] 2.5 Testes de modelo e regras de negócio

## 3. App `lancamentos`
- [ ] 3.1 Modelo de Lançamento com Tipo e Status calculado (property + QuerySet customizado)
- [ ] 3.2 Implementar os 9 tipos de lançamento e suas regras de direção/propagação
- [ ] 3.3 Restringir Conciliação a criação automática (não manual)
- [ ] 3.4 Restringir Aporte/Resgate a contas Investimento
- [ ] 3.5 Testes de cálculo de status (Previsto/Pendente/Pago)

## 4. App `parcelas`
- [ ] 4.1 Geração automática de N lançamentos Parcela de Cartão a partir de uma compra
- [ ] 4.2 Vencimento de cada parcela seguindo o dia configurado na conta Cartão
- [ ] 4.3 Descrição automática com progresso (`1/10`, `2/10`, ...)
- [ ] 4.4 Testes de geração de parcelas

## 5. App `meses`
- [ ] 5.1 Modelo de controle de meses criados (ex.: `MesAberto`)
- [ ] 5.2 Service layer de criação de mês com propagação por tipo
- [ ] 5.3 Vínculo de série recorrente (`grupo_recorrencia`) entre instâncias propagadas
- [ ] 5.4 Cascata de edição (sobrescreve customização futura) e exclusão (remove
      instâncias futuras) de lançamentos recorrentes
- [ ] 5.5 Tratamento de lançamentos pendentes do mês anterior na criação do novo mês
- [ ] 5.6 Cálculo de saldo encadeado (saldo_inicial armazenado por conta/mês) e
      geração automática de Conciliação
- [ ] 5.7 Aviso ao ultrapassar o limite de 12 meses futuros (sem bloqueio)
- [ ] 5.8 Testes de propagação, cascata e cálculo de saldo

## 6. App `visualizacao`
- [ ] 6.1 Visão de conta
- [ ] 6.2 Visão consolidada (Banco + Cartão)
- [ ] 6.3 Visão de patrimonio (Investimento)
- [ ] 6.4 Navegação entre meses (seletor + anterior/próximo)
- [ ] 6.5 Confirmação ao editar mês encerrado
- [ ] 6.6 Comparativo entre meses (padrão: atual vs. anterior)
- [ ] 6.7 Ações inline (Pagar/Editar/Excluir) via HTMX

## 7. Admin e finalização
- [ ] 7.1 Configurar Django Admin para contas/lançamentos
- [ ] 7.2 Revisão geral e `openspec validate setup-inicial`
- [ ] 7.3 `openspec archive setup-inicial` ao concluir
