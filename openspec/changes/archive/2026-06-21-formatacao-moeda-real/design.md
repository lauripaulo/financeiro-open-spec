## Context

O projeto é Django 5.1 com `LANGUAGE_CODE = 'pt-br'`, sem `USE_THOUSAND_SEPARATOR`, sem `django.contrib.humanize`, sem CSS framework (CSS próprio em `templates/base.html`) e sem nenhuma dependência JS além do HTMX via CDN. Não existe pasta `static/` nem `STATICFILES_DIRS` configurado. Os campos monetários (`Conta.saldo_atual`, `Conta.limite_negativo`, `Lancamento.valor`, `CompraParcelada.valor_total`, `Mes.saldo_inicial`) são todos `DecimalField(max_digits=14, decimal_places=2)`, expostos hoje via `ModelForm`/`Form` padrão (widget `NumberInput`) e exibidos via interpolação direta (`{{ valor }}`) nos templates.

Os testes existentes (`contas/tests.py`, `lancamentos/tests.py`, `parcelas/tests.py`, `meses/tests.py`) fazem POST de strings decimais simples (ex: `"valor": "50.00"`, ponto decimal, sem separador de milhar) e não devem precisar de nenhuma alteração.

## Goals / Non-Goals

**Goals:**
- Exibir todo valor monetário no padrão brasileiro: `R$ 1.234,56`.
- Aplicar máscara de digitação em todos os campos de entrada monetários, formatando em tempo real no mesmo padrão, com "R$" como elemento visual fixo fora do valor editável.
- Preservar 100% o contrato de validação/parsing do backend (`DecimalField` continua recebendo `1234.56`), sem precisar tocar nos testes existentes.

**Non-Goals:**
- Não ativar `USE_THOUSAND_SEPARATOR` global nem `django.contrib.humanize` — afetaria todos os números do sistema, não só os monetários.
- Não mudar o schema dos models nem adicionar `localize=True` aos `DecimalField` dos forms.
- Não introduzir biblioteca JS externa (ex: IMask, Cleave.js) — o stack atual só usa HTMX via CDN; uma máscara de moeda em vanilla JS é simples o suficiente para não justificar uma nova dependência.

## Decisions

**1. Filtro de template dedicado (`moeda`) em vez de formatação global.**
Alternativa considerada: `USE_THOUSAND_SEPARATOR = True` no settings. Rejeitada porque formataria qualquer número renderizado em template (IDs, contagens, percentuais), não só valores monetários — efeito colateral amplo para um requisito que é especificamente sobre dinheiro. Um filtro explícito (`{{ valor|moeda }}`), aplicado só nos templates/campos listados no proposal, é mais previsível.

**2. Formatação por manipulação de string, não pelo módulo `locale`.**
`locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')` depende do locale estar instalado no SO/container, uma fonte comum de falhas inconsistentes entre dev/CI/produção. A função do filtro implementa o agrupamento de milhar e troca de separador manualmente, sem depender de locale do sistema.

**3. Mascaramento 100% no front-end (JS), backend inalterado.**
Em vez de fazer o Django aceitar formato brasileiro (`localize=True` nos `DecimalField`), a máscara só formata visualmente; antes do `submit`, o JS reescreve o próprio `value` do input de `"1.234,56"` para `"1234.56"`. Isso evita qualquer mudança em `forms.py` além do widget, e mantém os testes existentes (que fazem POST direto via `Client`, sem JS) passando sem alteração.

**4. Novo `MoedaWidget(forms.TextInput)` em vez de customizar `NumberInput`.**
`<input type="number">` não aceita formato com separador de milhar/decimal customizado (o browser rejeita o valor). Trocar para `type="text"` com `inputmode="decimal"` permite a máscara livre, mantendo teclado numérico em mobile.

**5. "R$" como elemento puramente visual, fora do `value` do input.**
Como os forms são renderizados via `{{ form.as_p }}` (sem controle granular por campo), o prefixo "R$" é injetado via JS (envolvendo o input num wrapper com um `<span>` de prefixo) em vez de no HTML server-side do widget — mantém o widget Django simples e concentra toda a lógica de apresentação do prefixo em um único arquivo JS.

**6. Localização do filtro: app `visualizacao`. Localização do widget: app `contas`.**
`visualizacao` é o app que só faz apresentação (depende de todos os outros, nenhum depende dele) — lugar natural para um filtro de exibição. O widget, por sua vez, é consumido por `contas/forms.py` e `lancamentos/forms.py`; como `lancamentos/forms.py` já importa de `contas.models`, colocar o widget em `contas/widgets.py` não introduz nenhuma dependência nova/circular.

## Risks / Trade-offs

- **[Risco] Usuário desabilita JS no navegador** → campo de texto sem máscara aceita qualquer string; a validação do `DecimalField` no backend já rejeita formato inválido, então o pior caso é uma mensagem de erro de validação em vez de submissão silenciosamente errada. Mitigação: nenhuma ação adicional necessária, o backend já é a fonte de verdade.
- **[Risco] Formulário recarregado via HTMX (`hx-swap`) sem re-disparar o JS de máscara** → hoje nenhum dos forms com campo monetário (`ContaForm`, `LancamentoForm`, `CompraParceladaForm`) é trocado via HTMX (`hx-post` é usado só em ações como marcar pago/excluir/transferir, que não envolvem esses campos) → sem mitigação necessária no momento; risco futuro se algum desses forms passar a ser carregado via swap HTMX.
- **[Trade-off] Cursor pula para o final do input a cada tecla digitada** (a formatação reconstrói o valor a partir dos dígitos a cada `input` event) → aceito como compromisso de simplicidade; é comportamento comum em máscaras de valor monetário e não impede a digitação contínua de números.

## Migration Plan

Mudança aditiva, sem migration de banco de dados. Pode ser implantada em um único deploy:
1. Filtro de template e widget são código novo, sem afetar comportamento até serem referenciados nos templates/forms.
2. Aplicar nos templates/forms listados no proposal.
3. Rollback trivial: revert do commit (nenhuma migration ou dado persistido é afetado).

## Open Questions

Nenhuma — decisões de exibição (filtro dedicado), prefixo "R$" (fora do valor) e contrato de backend (decimal puro) já foram validadas com o usuário antes deste design.
