## 1. Filtro de exibicao `moeda`

- [ ] 1.1 Criar `visualizacao/templatetags/__init__.py`
- [ ] 1.2 Criar `visualizacao/templatetags/moeda.py` com o filtro `moeda` (Decimal/None/string -> "R$ 1.234,56", None/"" -> "R$ 0,00", invalido -> "", negativo -> "-R$ ...")
- [ ] 1.3 Adicionar testes unitarios do filtro em `visualizacao/tests.py` (valor simples, sem decimais, negativo, milhoes, None, string vazia, invalido)

## 2. Aplicar o filtro nos templates de exibicao

- [ ] 2.1 `templates/visualizacao/comparativo.html`: `{% load moeda %}` + aplicar filtro em `saldo_a`, `saldo_b`, `variacao`
- [ ] 2.2 `templates/visualizacao/consolidada.html`: `{% load moeda %}` + aplicar filtro em `valor_absoluto` (mantendo `+`/`-` literal fora do filtro), `total_entradas`, `total_saidas`, `saldo_total`
- [ ] 2.3 `templates/visualizacao/patrimonio.html`: `{% load moeda %}` + aplicar filtro em `item.saldo`, `mov.valor`
- [ ] 2.4 `templates/contas/lista.html`: `{% load moeda %}` + aplicar filtro em `saldo_atual`, `limite_negativo` (remover `|default:"-"`)
- [ ] 2.5 Adicionar testes de smoke de renderizacao (asserts de string "R$ " formatada) para as views de `contas:listar`, `consolidada`, `patrimonio` em `visualizacao/tests.py`

## 3. Widget de mascara de entrada

- [ ] 3.1 Criar `contas/widgets.py` com `MoedaWidget(forms.TextInput)`: `class="money-input"`, `inputmode="decimal"`, `format_value()` formatando Decimal/string para "1.234,56" (vazio permanece vazio)
- [ ] 3.2 Adicionar teste de `MoedaWidget.format_value` em `contas/tests.py` (Decimal -> "256.432,11", None -> "")

## 4. JS de mascara e assets estaticos

- [ ] 4.1 Adicionar `STATICFILES_DIRS = [BASE_DIR / 'static']` em `financeiro/settings.py`
- [ ] 4.2 Criar `static/js/money-mask.js`: no `DOMContentLoaded`, envolver cada `input.money-input` num wrapper com prefixo visual "R$"; formatar em tempo real no evento `input`; no evento `submit` do form pai, reescrever o value do input para decimal puro (ex: "1234.56") antes do envio
- [ ] 4.3 Em `templates/base.html`: adicionar `{% load static %}` na primeira linha, incluir `<script src="{% static 'js/money-mask.js' %}"></script>` apos o script do HTMX, adicionar CSS `.money-field`/`.money-prefix`/`.money-input` no bloco `<style>` existente

## 5. Aplicar o widget nos formularios

- [ ] 5.1 `contas/forms.py`: `ContaForm.Meta.widgets = {"saldo_atual": MoedaWidget(), "limite_negativo": MoedaWidget()}`
- [ ] 5.2 `lancamentos/forms.py`: `LancamentoForm.Meta.widgets = {"valor": MoedaWidget()}`
- [ ] 5.3 `lancamentos/forms.py`: `CompraParceladaForm.valor_total` -> `forms.DecimalField(max_digits=14, decimal_places=2, widget=MoedaWidget())`

## 6. Verificacao

- [ ] 6.1 Rodar `python manage.py test` e confirmar que a suite existente (`contas`, `lancamentos`, `parcelas`, `meses`) permanece verde sem nenhuma alteracao nesses arquivos de teste
- [ ] 6.2 Rodar `python manage.py runserver`, abrir os formularios de criacao/edicao de conta e lancamento, digitar valores e confirmar a mascara em tempo real ("R$" visivel, formatacao "1.234,56") e que o submit salva o valor correto
- [ ] 6.3 Verificar visualmente as telas de Visao consolidada, Patrimonio, Comparativo e Contas exibindo valores no formato "R$ 1.234,56"
