## 1. Filtro de exibicao `moeda`

- [x] 1.1 Criar `visualizacao/templatetags/__init__.py`
- [x] 1.2 Criar `visualizacao/templatetags/moeda.py` com o filtro `moeda` (Decimal/None/string -> "R$ 1.234,56", None/"" -> "R$ 0,00", invalido -> "", negativo -> "-R$ ...")
- [x] 1.3 Adicionar testes unitarios do filtro em `visualizacao/tests.py` (valor simples, sem decimais, negativo, milhoes, None, string vazia, invalido)

## 2. Aplicar o filtro nos templates de exibicao

- [x] 2.1 `templates/visualizacao/comparativo.html`: `{% load moeda %}` + aplicar filtro em `saldo_a`, `saldo_b`, `variacao`
- [x] 2.2 `templates/visualizacao/consolidada.html`: `{% load moeda %}` + aplicar filtro em `valor_absoluto` (mantendo `+`/`-` literal fora do filtro), `total_entradas`, `total_saidas`, `saldo_total`
- [x] 2.3 `templates/visualizacao/patrimonio.html`: `{% load moeda %}` + aplicar filtro em `item.saldo`, `mov.valor`
- [x] 2.4 `templates/contas/lista.html`: `{% load moeda %}` + aplicar filtro em `saldo_atual`, `limite_negativo` (remover `|default:"-"`)
- [x] 2.5 Adicionar testes de smoke de renderizacao (asserts de string "R$ " formatada) para as views de `contas:listar`, `consolidada`, `patrimonio` em `visualizacao/tests.py`

## 3. Widget de mascara de entrada

- [x] 3.1 Criar `contas/widgets.py` com `MoedaWidget(forms.TextInput)`: `class="money-input"`, `inputmode="decimal"`, `format_value()` formatando Decimal/string para "1.234,56" (vazio permanece vazio)
- [x] 3.2 Adicionar teste de `MoedaWidget.format_value` em `contas/tests.py` (Decimal -> "256.432,11", None -> "")

## 4. JS de mascara e assets estaticos

- [x] 4.1 Adicionar `STATICFILES_DIRS = [BASE_DIR / 'static']` em `financeiro/settings.py`
- [x] 4.2 Criar `static/js/money-mask.js`: no `DOMContentLoaded`, envolver cada `input.money-input` num wrapper com prefixo visual "R$"; formatar em tempo real no evento `input`; no evento `submit` do form pai, reescrever o value do input para decimal puro (ex: "1234.56") antes do envio
- [x] 4.3 Em `templates/base.html`: adicionar `{% load static %}` na primeira linha, incluir `<script src="{% static 'js/money-mask.js' %}"></script>` apos o script do HTMX, adicionar CSS `.money-field`/`.money-prefix`/`.money-input` no bloco `<style>` existente

## 5. Aplicar o widget nos formularios

- [x] 5.1 `contas/forms.py`: `ContaForm.Meta.widgets = {"saldo_atual": MoedaWidget(), "limite_negativo": MoedaWidget()}`
- [x] 5.2 `lancamentos/forms.py`: `LancamentoForm.Meta.widgets = {"valor": MoedaWidget()}`
- [x] 5.3 `lancamentos/forms.py`: `CompraParceladaForm.valor_total` -> `forms.DecimalField(max_digits=14, decimal_places=2, widget=MoedaWidget())`

## 6. Verificacao

- [x] 6.1 Rodar `python manage.py test` e confirmar que a suite existente (`contas`, `lancamentos`, `parcelas`, `meses`) permanece verde sem nenhuma alteracao nesses arquivos de teste (72/72 passando)
- [x] 6.2 Rodar `python manage.py runserver` e confirmar via curl que os formularios de conta renderizam o widget (`class="money-input"`, `type="text"`) e que `static/js/money-mask.js` e servido corretamente. Nao foi feito teste interativo em navegador real (digitacao ao vivo) — apenas verificacao de markup/serving e revisao de codigo do JS.
- [x] 6.3 Verificado via curl que as telas de Visao consolidada, Patrimonio e Contas exibem valores no formato "R$ 1.234,56" usando dados reais do banco local (ex: "R$ 25.000,00", "+R$ 25.000,00", "-R$ 550,00")
