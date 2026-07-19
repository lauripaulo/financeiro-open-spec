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
- **Importacao de arquivo** — trazer transacoes de um arquivo OFX (fatura do
  cartao ou extrato da conta corrente) para dentro do sistema como
  lancamentos da conta escolhida.
- **Extrato de conta** — transacoes ja efetivadas da conta corrente; item
  importado de extrato nasce pago na data em que ocorreu.
- **Detalhes** — texto complementar opcional do lancamento; guarda o memo
  integral do banco quando a importacao encurta a descricao. Listagens
  mostram apenas a descricao.
- **Pagamento de fatura (importacao)** — a quitacao da fatura aparece nas
  duas pontas (recebimento no cartao, debito na conta) e e pulada em ambas
  as importacoes para nao duplicar os gastos do cartao.
- **Item importado** — rastro de uma transacao ja importada; permite que
  importacoes seguintes reconhecam o que ja existe (deduplicacao).
- **Identificador da compra (FITID)** — codigo que o banco atribui a compra;
  o mesmo codigo acompanha todas as parcelas da compra em faturas seguintes.
- **Parcela projetada** — parcela futura criada pela importacao com valor
  estimado; corrigida quando a fatura real do mes chegar.
- **Modo de importacao** — escolha do usuario a cada importacao: somente
  itens novos, ou sobrescrever projecoes existentes com os dados reais.
  Lancamento ja pago nunca e sobrescrito.
