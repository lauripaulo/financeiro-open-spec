# Tasks: paginar-movimentacoes-consolidada

## 1. View

- [x] 1.1 Em `visualizacao/views.py::visao_consolidada`, paginar
      `resumo.lancamentos` com `django.core.paginator.Paginator` (50 por
      pagina) usando `paginator.get_page(request.GET.get("pagina"))`;
      entregar `page_obj` ao contexto no lugar da lista completa exibida
      na tabela, mantendo os agregados de `ResumoMes` intocados.

## 2. Template

- [x] 2.1 Em `templates/visualizacao/consolidada.html`, iterar `page_obj`
      na tabela de Movimentacoes (totais continuam lendo os agregados do
      contexto).
- [x] 2.2 Adicionar controle "Anterior / Pagina X de Y / Proxima" abaixo da
      tabela, estilo `m3-button--text`, renderizado apenas quando
      `page_obj.paginator.num_pages > 1`; links reconstroem a querystring
      com `ano`, `mes`, `conta` e `status` ativos mais `pagina` alvo.

## 3. Testes

- [x] 3.1 Teste: mes com 51 lancamentos — pagina 1 exibe 50, pagina 2 exibe 1.
- [x] 3.2 Teste: totais de Entradas/Saidas/Saldo identicos nas paginas 1 e 2
      (mes inteiro).
- [x] 3.3 Teste: `?pagina=abc` exibe pagina 1; `?pagina=999` clampa para a
      ultima pagina.
- [x] 3.4 Teste: links do controle preservam `ano`, `mes`, `conta`, `status`
      (`assertContains`).
- [x] 3.5 Teste: com 50 lancamentos ou menos, controle de paginacao nao e
      renderizado.

## 4. Verificacao

- [x] 4.1 Rodar `.venv/bin/python manage.py test visualizacao` e suite
      completa `.venv/bin/python manage.py test`.
- [x] 4.2 `openspec validate --changes` sem erros.
