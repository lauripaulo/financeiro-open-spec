# 0001 — Deduplicacao de importacao OFX por FITID, nao por hash de conteudo

Data: 2026-07-19
Status: aceito

## Contexto

A importacao de fatura OFX do cartao Nubank precisa reconhecer, em
importacoes sucessivas, quais transacoes ja existem no sistema. O pedido
original era um hash de `titulo + data + valor`.

A analise de dois arquivos reais consecutivos (`import/nubank-card-ofx` e
`import/nubank-card-2.ofx`) revelou duas propriedades do formato Nubank:

1. **FITID identifica a compra, nao a transacao.** Todas as parcelas de uma
   mesma compra carregam o mesmo FITID em faturas de meses diferentes
   (ex.: `Idoc3d - Parcela 1/3` e `Parcela 2/3`, mesmo FITID `6a54db8f...`).
2. **Valor e data de parcelas variam entre faturas.** O Nubank distribui o
   arredondamento de forma propria (296,68 na parcela 1, 296,66 na 2), entao
   qualquer chave que inclua valor/data nunca casaria a parcela projetada
   com a parcela real do mes seguinte.

Alem disso, um hash `titulo + data + valor` colapsaria compras legitimas
identicas no mesmo dia (caso real: duas compras "M6 Comercio de Confecc -
Parcela 1/3" na mesma data — apenas o FITID as distingue).

Ressalva: FITID sozinho nao basta — o Nubank reusa o FITID da compra na
linha de IOF correspondente (memos diferentes, mesmo FITID).

## Decisao

Chave de deduplicacao gravada em `ItemImportado.chave_dedup`:

- Parcela de compra parcelada: `sha256(conta_id | fitid | parcela_atual)`
  — valor e data ficam fora da chave de proposito, para que a parcela real
  case com a projetada e possa corrigi-la (modo sobrescrever).
- Demais transacoes: `sha256(conta_id | fitid | memo)` — memo diferencia o
  par IOF/compra que compartilha FITID.

A importacao de compra parcelada cria as parcelas futuras como projecao
(mesmo valor da parcela atual) e registra um `ItemImportado` para cada uma,
para que a fatura seguinte as encontre e corrija.

## Consequencias

- Reimportar o mesmo arquivo e idempotente em qualquer modo.
- O modo "sobrescrever" corrige valor/vencimento de projecoes; lancamento
  ja pago nunca e alterado.
- A chave depende de o banco manter FITID estavel por compra. Importadores
  de outros bancos precisarao rever essa premissa (a chave fica encapsulada
  no servico de importacao).
