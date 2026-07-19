# Proposal: importar-ofx-conta-nubank

## Why

O sistema ja importa OFX do cartao Nubank (menu Importar), mas o extrato da conta corrente ainda precisa ser lancado a mao. O mesmo formato OFX esta disponivel para a conta (`import/nubank-conta.ofx`) e a infraestrutura de importacao (parser SGML, dedup por FITID via `ItemImportado`, telas) ja existe — falta so o fluxo da conta corrente.

## What Changes

- Nova opcao "OFX da conta Nubank" na pagina Importar, com form proprio (arquivo + conta tipo Banco + modo de importacao).
- Novo servico `importar_ofx_nubank_conta`: DEBIT vira Gasto Variavel, CREDIT vira Recebimento Excepcional; lancamento nasce pago (`data_pagamento = data_vencimento = DTPOSTED`), pois extrato e fato consumado.
- Transacao `Pagamento de fatura` (DEBIT) e pulada — e a outra ponta do `Pagamento recebido` ja pulado na importacao do cartao (mesmo FITID); importar duplicaria os gastos do cartao.
- Sem logica de parcelas na conta corrente (memo `- Parcela X/Y` e tratado como item simples).
- Mes de competencia (mes do DTPOSTED) deve estar aberto para todos os itens; import atomico cancela tudo se houver mes fechado.
- Dedup reutiliza `ItemImportado` com chave `sha256(conta_id | fitid | memo)`.

## Capabilities

### New Capabilities
- `importacao-ofx-conta`: importacao de extrato OFX da conta corrente Nubank — mapeamento de tipos, item nasce pago, pulo de pagamento de fatura, deduplicacao por FITID e exigencia de mes aberto.

### Modified Capabilities
<!-- nenhuma: nao ha spec existente de importacao (o fluxo do cartao foi implementado antes do openspec cobrir a area) e nenhum requisito de outra capability muda -->

## Impact

- `importacao/services.py` — novo servico + reuso do parser e helpers de dedup existentes.
- `importacao/forms.py`, `views.py`, `urls.py` — form/view/rota novos.
- `templates/importacao/` — card novo no indice; form generalizado ou template novo.
- `importacao/tests.py` — suite espelhando a do cartao para conta corrente.
- Sem migracao de banco (modelos existentes bastam) e sem dependencia nova.
- `CONTEXT.md` — generalizar termo de importacao (fatura de cartao + extrato de conta).
