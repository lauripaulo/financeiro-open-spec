# Design: importar-ofx-conta-nubank

## Context

O app `importacao` ja implementa o fluxo do cartao Nubank: `parse_ofx_nubank()` (parser SGML proprio), `ItemImportado` (dedup por `chave_dedup` sha256), modos NOVOS/SOBRESCREVER, pagina indice + form + resultado via sessao. O OFX da conta corrente (`import/nubank-conta.ofx`, secao `BANKMSGSRSV1`) e lido pelo parser atual sem mudanca — `ACCTID` e blocos `STMTTRN` identicos.

Diferencas de dominio da conta corrente frente ao cartao:
- Conta destino e tipo `BANCO` (sem `dia_vencimento`).
- Transacao de extrato ja aconteceu — nasce paga.
- Nao existem parcelas.
- A ponta do pagamento de fatura aqui e DEBIT `"Pagamento de fatura"` (mesmo FITID do `"Pagamento recebido"` do cartao, confirmado nos arquivos reais).

Decisoes fixadas em grilling com o usuario: pular pagamento de fatura; nascer pago; DEBIT→GASTO_VARIAVEL / CREDIT→RECEBIMENTO_EXCEPCIONAL sem detectar transferencias internas.

## Goals / Non-Goals

**Goals:**
- Importar extrato da conta Nubank com a mesma UX e garantias do cartao (dedup, atomicidade, resumo).
- Reusar parser, chaves de dedup e telas existentes; zero migracao de banco.

**Non-Goals:**
- Detectar transferencias internas entre contas do sistema (Pix para conta propria vira gasto/recebimento comum; usuario ajusta manualmente se quiser).
- Conciliar saldo (`LEDGERBAL`) com `Conta.saldo_atual`.
- Parcelamento na conta corrente.
- Suporte a OFX de outros bancos.

## Decisions

1. **Servico proprio `importar_ofx_nubank_conta`, compartilhando helpers** — em vez de um servico unico com flag de origem. O fluxo da conta e mais curto (sem parcelas, sem calculo de vencimento por dia da fatura); flag unica criaria ramos mortos e acoplaria os dois fluxos. Compartilha: `parse_ofx_nubank`, `chave_dedup_simples`, `_item_resumo`, `_sha256`, modelo `ItemImportado`.
2. **`_tratar_existente` nao e reusado no fluxo da conta** — ele calcula vencimento por `conta.dia_vencimento` (None em banco). Como item de conta nasce pago e pago nunca e sobrescrito, o tratamento de existente na conta reduz a: NOVOS → "ja importado"; SOBRESCREVER → "ja pago" (ou "lancamento original excluido"). Logica local simples no servico da conta.
3. **Guard de pagamento de fatura por memo exato + TRNTYPE** — `"Pagamento de fatura"` + DEBIT, simetrico ao guard `"Pagamento recebido"` + CREDIT do cartao. Alternativa (casar FITID entre importacoes das duas pontas) rejeitada: acopla ordem de importacao dos arquivos.
4. **`data_vencimento = data_pagamento = DTPOSTED`** — status Pago derivado, coerente com "extrato e fato consumado". Alternativa (nascer nao pago) rejeitada: itens passados virariam PENDENTE e poluiriam pendencias.
5. **Template de form unico parametrizado** — generalizar `nubank_cartao_form.html` para receber titulo/ajuda via contexto da view, evitando template duplicado. Card novo no `index.html`.
6. **Form com base comum** — extrair decode (utf-8 → fallback cp1252) para classe base; `ImportacaoOFXNubankContaForm` filtra `tipo=BANCO`.

## Risks / Trade-offs

- [Memo do guard mudar no Nubank] → guard e string exata num unico lugar; teste com arquivo real documenta o formato. Se mudar, item vira gasto comum e usuario ve na tela de resultado — falha visivel, nao silenciosa.
- [Pix interno vira gasto/recebimento comum] → aceito de proposito (Non-Goal); pode inflar gasto variavel do mes. Usuario pode excluir/editar o lancamento.
- [FITID da conta reutilizado pelo banco em contextos distintos] → chave inclui memo, mesmo padrao ja validado no cartao (par IOF/compra).
- [Item de conta importado nunca e corrigivel por sobrescrever (nasce pago)] → comportamento desejado pela regra "pago nao sobrescreve"; correcao manual continua possivel na tela de lancamentos.

## Migration Plan

Sem migracao de schema. Deploy normal; rollback = reverter commit (nenhum dado novo alem de `Lancamento`/`ItemImportado` criados por importacoes ja executadas).

## Open Questions

Nenhuma — decisoes de produto fechadas em grilling (registradas no proposal e no CONTEXT.md).
