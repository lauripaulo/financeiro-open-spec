# Tasks: importar-ofx-conta-nubank

## 1. Servico de importacao da conta

- [x] 1.1 Criar `importar_ofx_nubank_conta(*, conta, texto, modo)` em `importacao/services.py` (atomico): guard DEBIT+"Pagamento de fatura" pulado; DEBIT→GASTO_VARIAVEL, CREDIT→RECEBIMENTO_EXCEPCIONAL; `data_vencimento = data_pagamento = DTPOSTED`; competencia do DTPOSTED; `gerado_automaticamente=True`; sem logica de parcelas
- [x] 1.2 Dedup com `chave_dedup_simples` + `ItemImportado` (acctid gravado); existente: NOVOS→"ja importado", SOBRESCREVER→"ja pago"/"lancamento original excluido"
- [x] 1.3 Mes aberto obrigatorio para todo item novo; acumular meses fechados e cancelar com ValidationError listando-os

## 2. Form, view, rotas e templates

- [x] 2.1 Extrair base comum de decode (utf-8→cp1252) em `importacao/forms.py` e criar `ImportacaoOFXNubankContaForm` com queryset `tipo=BANCO`
- [x] 2.2 View `importar_nubank_conta` + rota `nubank-conta/` (name `nubank_conta`) reutilizando sessao de resumo e pagina de resultado
- [x] 2.3 Generalizar template de form (titulo/ajuda/action via contexto) e adicionar card "OFX da conta Nubank" em `templates/importacao/index.html`

## 3. Testes

- [x] 3.1 Servico: DEBIT pago como GASTO_VARIAVEL, CREDIT pago como RECEBIMENTO_EXCEPCIONAL, datas/competencia/status Pago
- [x] 3.2 Guards: "Pagamento de fatura" DEBIT pulado; mesmo memo como CREDIT importado; memo "- Parcela 2/3" nao cria CompraParcelada
- [x] 3.3 Dedup: reimportacao idempotente; sobrescrever reporta "ja pago" sem alterar; lancamento excluido reportado
- [x] 3.4 Mes fechado cancela import inteiro sem gravar
- [x] 3.5 Form: conta CARTAO rejeitada; decode cp1252/utf-8
- [x] 3.6 Views: card no indice, fluxo de upload completo, erro de mes fechado no form

## 4. Dominio e verificacao

- [x] 4.1 Atualizar `CONTEXT.md`: generalizar importacao (fatura de cartao + extrato de conta), registrar "item de extrato nasce pago" e pulo das duas pontas do pagamento de fatura
- [x] 4.2 Rodar suite completa (`manage.py test`) verde
- [x] 4.3 Smoke com `import/nubank-conta.ofx` real em transacao com rollback: 33 criados + 1 pulado (Pagamento de fatura); reimportacao → 0 criados
