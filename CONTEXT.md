# Glossario

Linguagem ubiqua do dominio. Somente termos e significados — sem detalhes de
implementacao.

- **Conta** — origem/destino de movimentacoes. Tres tipos: Banco, Cartao,
  Investimento. Investimento fica fora das visoes consolidadas de Banco/Cartao.
- **Lancamento** — registro financeiro de um mes de competencia, com tipo,
  direcao (entrada/saida) e status.
- **Status** — situacao calculada de um lancamento (Previsto, Pendente, Pago);
  nunca armazenada nem editada diretamente.
- **Pagar** — marcar lancamento como pago com data explicita de pagamento;
  pagamento e sempre integral.
- **Lancamento vinculado** — par interno criado pelo fluxo de transferencia
  entre contas; nao e conceito editavel pelo usuario.
- **Transferencia** — operacao que cria um par de lancamentos vinculados
  (enviada na origem, recebida no destino) com o mesmo valor.
- **Pendentes do mes anterior** — lancamentos nao pagos do mes fechado
  aguardando decisao do usuario: transferir para o mes atual ou manter.
- **Mes** — unidade de competencia; abre sequencialmente (somente o mes
  seguinte ao ultimo aberto) e propaga lancamentos recorrentes.
- **Compra parcelada** — compra de cartao que gera parcelas mensais; unica
  origem de lancamentos do tipo Parcela de Cartao.
- **Importacao de fatura** — trazer transacoes de um arquivo OFX do cartao
  para dentro do sistema como lancamentos da conta escolhida.
- **Item importado** — rastro de uma transacao ja importada; permite que
  importacoes seguintes reconhecam o que ja existe (deduplicacao).
- **Identificador da compra (FITID)** — codigo que o banco atribui a compra;
  o mesmo codigo acompanha todas as parcelas da compra em faturas seguintes.
- **Parcela projetada** — parcela futura criada pela importacao com valor
  estimado; corrigida quando a fatura real do mes chegar.
- **Modo de importacao** — escolha do usuario a cada importacao: somente
  itens novos, ou sobrescrever projecoes existentes com os dados reais.
  Lancamento ja pago nunca e sobrescrito.
