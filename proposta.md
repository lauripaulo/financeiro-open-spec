# Software para Controle Financeiro Pessoal

Este documento descreve um sistema de controle financeiro pessoal que tem como objetivo controlar
os gastos do mês atual, consultar os gastos de meses passados e prever os gastos de meses futuros.

Deve ser possível estimar quais serão as contas, recebimentos, parcelas e assinaturas e seu valor
total de saldo para meses futuros.

Deve mostrar a projeção de gastos para o mês atual, indicando quais lançamentos estão previstos,
quais já foram pagos e quais estão pendentes de pagamento (data de vencimento já passou mas
ainda não foram pagos).

Deve ser possível visualizar os lançamentos do mês por conta, mostrando apenas os lançamentos
dentro da mesma conta. Essa visão é chamada de *Visão de conta*.

Também deve ser possível ver todos os lançamentos do mês de todas as contas em ordem de data
de vencimento, com uma coluna para identificar a qual conta cada lançamento pertence. Essa visão
é chamada de *Visão consolidada*. A Visão consolidada reúne apenas as contas do tipo **Banco** e
**Cartão**, já que essas são as contas que compõem o saldo corrente do mês. Contas do tipo
**Investimento** têm uma visão própria, descrita na seção *Contas de investimento* mais abaixo.

O sistema terá um cadastro de contas. A primeira coisa que deve ser feita no sistema é criar uma
conta para poder realizar lançamentos. Uma conta não pode ser apagada se ela possui lançamentos
associados, independentemente do status desses lançamentos.

---

# Contas

Contas são agrupamentos de entradas e saídas financeiras. Existem três tipos de conta, cada um
com campos específicos. Para os tipos **Banco** e **Investimento**, o usuário informa o saldo
atual no momento da criação da conta — esse valor é o ponto de partida da conta e é herdado pelo
primeiro mês que vier a ser criado para ela (ver seção *Saldo e filtros*).

## Cartão

Representa um cartão de crédito. Campos:

  * Nome       - Nome da conta.
  * Tipo       - Cartão.
  * Vencimento - Dia do mês em que a fatura vence.

> Um campo de Limite de crédito para a conta Cartão (com o mesmo comportamento de alerta da
> conta Banco) foi avaliado e fica **fora de escopo** desta versão. Pode ser revisitado em
> versões futuras.

## Banco

Representa uma conta bancária. Campos:

  * Nome        - Nome da conta.
  * Tipo        - Banco.
  * Saldo atual - Valor informado pelo usuário na criação da conta, usado como saldo inicial.
  * Limite      - Valor máximo que o saldo pode ficar negativo (equivalente ao limite de cheque
                  especial). O sistema usa esse valor apenas como referência para **alertar** o
                  usuário quando o saldo se aproximar ou ultrapassar o limite negativo. O sistema
                  **não bloqueia** nenhuma ação por causa do limite — o lançamento é sempre
                  registrado, mesmo que o saldo fique mais negativo que o limite configurado.

## Investimento

Representa uma conta de acumulação de patrimônio, como previdência privada, CDB ou caderneta
de poupança. Campos:

  * Nome        - Nome da conta.
  * Tipo        - Investimento.
  * Saldo atual - Valor informado pelo usuário na criação da conta, usado como saldo inicial.

Contas de investimento registram apenas depósitos (entradas) e retiradas (saídas), por meio dos
tipos de lançamento *Aporte* e *Resgate* (ver seção *Tipos de lançamento*). Não possuem limite
nem vencimento.

O saldo acumulado de uma conta Investimento **não entra no saldo consolidado mensal** das contas
Banco e Cartão — é tratado separadamente, como acompanhamento de patrimônio. O sistema deve
oferecer uma visão própria para essas contas, mostrando o saldo acumulado e o histórico de
aportes e resgates, fora da Visão consolidada e da tela principal de saldo do mês.

---

# Lançamentos

São gastos ou recebimentos financeiros atrelados a uma conta. Formados por:

  * Descrição          - O que é esse lançamento financeiro.
  * Tipo               - Classifica o lançamento e determina se é uma entrada ou saída.
                         Ver seção *Tipos de lançamento*.
  * Data de vencimento - Data em que o lançamento está previsto ou deve ser pago.
  * Data de pagamento  - Data em que o lançamento foi efetivamente pago. Preenchida ao
                         marcar o lançamento como Pago.
  * Valor              - O valor monetário do lançamento.
  * Conta              - A qual conta esse lançamento pertence.
  * Status             - Estado atual do lançamento, somente leitura. Ver seção
                         *Status do lançamento*.

O pagamento de um lançamento é sempre **integral**; pagamento parcial não é suportado nesta
versão.

## Status do lançamento

O status é calculado automaticamente pelo sistema com base na data de vencimento e na data de
pagamento:

  * **Previsto**  - A data de vencimento ainda não chegou, ou é hoje, e o lançamento não foi pago.
  * **Pendente**  - O dia seguinte à data de vencimento já chegou e o lançamento ainda não foi pago.
  * **Pago**      - O lançamento possui uma data de pagamento registrada, independentemente da
                    data de vencimento.

A transição de Previsto para Pendente ocorre automaticamente a partir do dia seguinte à data de
vencimento, caso o lançamento não tenha sido pago até o fim do dia de vencimento.

---

# Tipos de lançamento

O tipo determina a natureza do lançamento e se ele representa uma entrada (valor que aumenta o
saldo) ou uma saída (valor que diminui o saldo). Também define se o lançamento é propagado
automaticamente ao criar um novo mês.

| Tipo                    | Direção | Propagado automaticamente |
|-------------------------|---------|----------------------------|
| Recebimento Fixo        | Entrada | Sim                        |
| Recebimento Excepcional | Entrada | Não                        |
| Gasto Fixo              | Saída   | Sim                        |
| Gasto Variável          | Saída   | Não                        |
| Assinatura              | Saída   | Sim                        |
| Parcela de Cartão       | Saída   | Sim (até o total)          |
| Conciliação             | Entrada ou Saída, conforme o sinal do ajuste | Não |
| Aporte (Investimento)   | Entrada | Não¹                       |
| Resgate (Investimento)  | Saída   | Não¹                       |

**Recebimento Excepcional** e **Gasto Variável** representam lançamentos que não ocorrem
regularmente todos os meses, como IPVA, IPTU, bônus salarial ou restituição de imposto de renda.
Por esse motivo, não são repetidos automaticamente ao criar um novo mês e devem ser cadastrados
manualmente quando ocorrerem. Podem ser cadastrados antecipadamente em meses futuros já criados,
permanecendo com status Previsto até a data de vencimento.

**Conciliação** é gerado automaticamente pelo próprio sistema quando o usuário ajusta o saldo
inicial herdado de um mês (ver seção *Saldo e filtros*), nunca é criado manualmente e nunca é
propagado para os meses seguintes.

**Aporte** e **Resgate** são exclusivos de contas do tipo Investimento e representam,
respectivamente, um depósito e uma retirada de valor acumulado.

> ¹ Este documento não levantou explicitamente se aportes recorrentes (ex.: uma previdência com
> contribuição mensal fixa) deveriam se propagar automaticamente como um Gasto Fixo. Por padrão,
> Aporte e Resgate são tratados como lançamentos manuais, cadastrados a cada ocorrência. Caso
> exista a necessidade de aportes automáticos recorrentes, este ponto deve ser revisitado.

---

# Parcelas

Parcelas representam compras divididas em pagamentos mensais, associadas a uma conta do tipo
*Cartão*. Ao registrar uma compra parcelada, o sistema cria automaticamente um lançamento do
tipo *Parcela de Cartão* para cada mês, iniciando no mês seguinte ao da compra, com vencimento no
mesmo dia configurado como Vencimento da conta Cartão.

Cada lançamento de parcela possui, além dos campos comuns de lançamento:

  * Total de parcelas - Quantidade total de pagamentos.
  * Parcela atual    - Número do pagamento referente ao mês (ex: 1, 2, 3...).

**Exemplo:** Uma compra de R$ 100,00 em janeiro parcelada em 10x gera 10 lançamentos de R$ 10,00
cada, do tipo Parcela de Cartão, com vencimentos de fevereiro a novembro. A descrição de cada
parcela indica o progresso, por exemplo: `Compra de notebook 1/10`, `Compra de notebook 2/10`,
e assim por diante.

O pagamento da fatura do Cartão é um lançamento independente, registrado manualmente pelo
usuário. O sistema **não** gera automaticamente uma saída vinculada na conta Banco quando uma
fatura é paga — se o usuário quiser refletir a saída do dinheiro da conta corrente, deve
cadastrar esse lançamento manualmente nela.

> Outros tipos de compra parcelada fora do cartão de crédito estão fora do escopo atual e podem
> ser contemplados em versões futuras do sistema.

---

# Registro de mês

Um mês reúne todos os lançamentos pagos, pendentes ou previstos para aquele período. Quando um
novo mês é criado, o mês anterior é usado como base para gerar os lançamentos do novo mês.
Todos os lançamentos gerados automaticamente iniciam com status **Previsto**.

A criação de um novo mês é sempre manual: o usuário decide quando criar. O sistema deve informar
que, para visualizar e editar um mês futuro, ele precisa ser criado primeiro. O sistema suporta
confortavelmente até 12 meses futuros; ao tentar criar um mês além desse limite, a criação não é
bloqueada, mas o sistema exibe um aviso ao usuário.

O primeiro mês do sistema é criado sem nenhum lançamento (não há mês anterior para servir de
base), mas **não** começa com saldo zero: o saldo inicial das contas Banco e Investimento é o
valor informado pelo usuário na criação de cada conta.

As seguintes regras de propagação se aplicam:

  1. Todos os lançamentos do tipo **Gasto Fixo** e **Recebimento Fixo** são repetidos para o
     mesmo dia no novo mês.
  2. Todos os lançamentos do tipo **Assinatura** são repetidos para o novo mês.
  3. Todos os lançamentos do tipo **Parcela de Cartão** que ainda não atingiram o total de
     parcelas são repetidos, e a parcela atual é acrescida de 1.

Os tipos **Recebimento Excepcional**, **Gasto Variável**, **Conciliação**, **Aporte** e
**Resgate** não são propagados automaticamente.

## Lançamentos pendentes do mês anterior

Ao criar um novo mês, o sistema exibe os lançamentos com status *Pendente* do mês anterior e
solicita ao usuário que decida o que fazer com cada um. O usuário pode optar por mantê-los no
mês anterior ou transferi-los para o novo mês.

## Edição de lançamentos recorrentes

Se o usuário editar um lançamento de um tipo propagável (Gasto Fixo, Recebimento Fixo ou
Assinatura) — por exemplo, alterando o valor do aluguel — a alteração é aplicada a **todas** as
instâncias desse lançamento já existentes em meses futuros já criados, **mesmo que** alguma
dessas instâncias futuras já tenha sido customizada manualmente: a edição em massa sobrescreve a
customização.

Se o usuário excluir um lançamento recorrente em um mês, o sistema **remove também** as
instâncias desse lançamento já criadas em meses futuros, além de deixar de propagá-lo daí em
diante.

---

# Entradas e saídas

O controle financeiro gira em torno de dois conceitos:

  * **Entrada:** Um valor positivo que aumenta o saldo de uma conta.
  * **Saída:** Um valor negativo que diminui o saldo de uma conta.

## Saldo e filtros

O saldo de uma conta Banco ou Cartão em um mês é calculado como:

```
saldo do mês = saldo inicial herdado do mês anterior
             + soma das entradas do período
             − soma das saídas do período
```

independentemente do status (Previsto, Pendente ou Pago) de cada lançamento. O usuário pode
aplicar filtros para visualizar apenas determinados status — por exemplo, excluir lançamentos
Pendentes — e o saldo é recalculado automaticamente conforme os filtros ativos.

O saldo final de uma conta em um mês é carregado automaticamente como o saldo inicial do mês
seguinte para essa mesma conta. O usuário pode editar esse saldo inicial herdado; ao fazer isso,
a diferença entre o valor herdado e o valor informado é registrada automaticamente pelo sistema
como um novo lançamento do tipo **Conciliação** no mês.

Contas do tipo Investimento seguem a mesma lógica de saldo acumulado (saldo anterior + Aportes −
Resgates), mas esse valor é exibido apenas na visão própria de patrimônio, sem entrar na soma do
saldo consolidado de Banco e Cartão.

## Exemplo

```
Dia: 01/04/2026
Conta: Banco do Brasil
Saldo inicial (herdado de março): R$ 0,00

Entrada de R$ 50,00 → saldo passa para R$ 50,00
Saída  de R$ 20,00 → saldo passa para R$ 30,00
```

A representação de entradas e saídas na tela principal segue o formato abaixo:

```
+--------------------------------------------------------------------------------------------------------------------------+
| Movimentações do mês de Abril de 2026 - Hoje é dia 03/04/2026             [ Novo lançamento ]                            |
+----------------------------+----------+----------+------------------+------------+---------------------------------------+
| Descrição                  | Entrada  | Saída    | Conta            | Data       | Status  | Ações                       |
+----------------------------+----------+----------+------------------+------------+---------+-----------------------------+
| Saldo inicial (herdado)    |          |          | Banco do Brasil  | 01/04/2026 |         |                             |
| Salário                    |   +50,00 |          | Banco do Brasil  | 01/04/2026 | Pago    | [Editar] [Excluir]          |
| Aluguel                    |          |   -30,00 | Banco do Brasil  | 02/04/2026 | Pendente| [Pagar] [Editar] [Excluir]  |
| Gasolina                   |          |   -10,00 | Banco do Brasil  | 03/04/2026 | Previsto| [Pagar] [Editar] [Excluir]  |
| Bônus                      |   +30,00 |          | Banco do Brasil  | 04/04/2026 | Previsto| [Pagar] [Editar] [Excluir]  |
+----------------------------+----------+----------+------------------+------------+---------+-----------------------------+
| TOTAL                      |   +80,00 |   -40,00 |
+----------------------------+----------+----------+
| SALDO (inicial + total)               |   +40,00 |
+---------------------------------------+----------+
```

---

# Histórico de meses passados

O usuário acessa um mês passado por meio de um seletor de mês e ano, ou pelos botões de
navegação anterior/próximo.

Meses passados podem ser editados, mediante confirmação do usuário: ao tentar editar um
lançamento de um mês já encerrado, o sistema pergunta "Você realmente quer editar um mês já
encerrado?" antes de aplicar a alteração.

Existe uma tela comparativa entre dois meses, com o mês atual e o mês anterior selecionados por
padrão; o usuário pode escolher outros meses para comparar.

---

# Limite da conta Banco

Quando o saldo de uma conta Banco ultrapassa o limite negativo configurado, o sistema **avisa**
o usuário, mas **não impede** o registro do lançamento. O limite é uma referência informativa,
não uma trava de negócio.