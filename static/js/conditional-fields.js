/* Campos condicionais declarativos.
 *
 * 1. Mostrar/esconder por selecao:
 *    <div class="m3-field" data-show-when="tipo=CARTAO">        (um valor)
 *    <div class="m3-field" data-show-when="tipo=BANCO|INVESTIMENTO"> (varios)
 *    O controlador e o campo #id_<nome> do mesmo <form>. Campo escondido
 *    recebe disabled (nao e submetido); o valor digitado permanece no DOM,
 *    entao reaparece se o usuario reverter a selecao antes de salvar.
 *    A validacao server-side (clean) segue sendo a fonte de verdade.
 *
 * 2. Filtro tipo->conta no formulario de lancamento:
 *    options de conta com data-conta-tipo="BANCO|CARTAO|INVESTIMENTO".
 *    Tipos exclusivos de Investimento chegam do servidor via atributo
 *    data-tipos-investimento no select de tipo (fonte unica:
 *    Lancamento.TIPOS_INVESTIMENTO). Esses tipos mostram apenas contas
 *    Investimento; os demais escondem contas Investimento. Options
 *    incompativeis sao removidas do DOM (option[hidden] nao funciona no
 *    Safari) e selecao incompativel e limpa.
 */
(function () {

    function setupShowWhen(form) {
        var wrappers = form.querySelectorAll("[data-show-when]");
        if (!wrappers.length) {
            return;
        }

        var groups = {};
        wrappers.forEach(function (wrapper) {
            var rule = wrapper.getAttribute("data-show-when");
            var parts = rule.split("=");
            var controllerName = parts[0];
            var values = parts[1].split("|");
            wrapper.querySelectorAll("input, select, textarea").forEach(function (el) {
                if (el.disabled) {
                    el.setAttribute("data-perma-disabled", "1");
                }
            });
            (groups[controllerName] = groups[controllerName] || []).push({
                wrapper: wrapper,
                values: values,
            });
        });

        Object.keys(groups).forEach(function (controllerName) {
            var controller = form.querySelector("#id_" + controllerName);
            if (!controller) {
                return;
            }

            function apply() {
                groups[controllerName].forEach(function (entry) {
                    var show = entry.values.indexOf(controller.value) !== -1;
                    entry.wrapper.classList.toggle("m3-field--hidden", !show);
                    entry.wrapper.querySelectorAll("input, select, textarea").forEach(function (el) {
                        if (el.hasAttribute("data-perma-disabled")) {
                            return;
                        }
                        el.disabled = !show;
                    });
                });
            }

            controller.addEventListener("change", apply);
            apply();
        });
    }

    function setupContaFilter(form) {
        var optionComTipo = form.querySelector("select option[data-conta-tipo]");
        if (!optionComTipo) {
            return;
        }
        var contaSelect = optionComTipo.closest("select");

        var tipoSelect = form.querySelector("#id_tipo");
        if (!tipoSelect) {
            return;
        }

        var tiposInvestimento = (tipoSelect.getAttribute("data-tipos-investimento") || "").split(",");
        var todasOptions = Array.prototype.slice.call(contaSelect.options);

        function apply() {
            var investimento = tiposInvestimento.indexOf(tipoSelect.value) !== -1;
            var selecionada = contaSelect.value;

            while (contaSelect.options.length) {
                contaSelect.remove(0);
            }
            todasOptions.forEach(function (option) {
                var contaTipo = option.getAttribute("data-conta-tipo");
                var compativel = !contaTipo || ( // opcao vazia ("---------") sempre visivel
                    investimento ? contaTipo === "INVESTIMENTO" : contaTipo !== "INVESTIMENTO"
                );
                if (compativel) {
                    contaSelect.add(option);
                }
            });

            contaSelect.value = selecionada;
            if (contaSelect.selectedIndex === -1) {
                contaSelect.value = "";
            }
        }

        tipoSelect.addEventListener("change", apply);
        apply();
    }

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll("form").forEach(function (form) {
            setupShowWhen(form);
            setupContaFilter(form);
        });
    });
})();
