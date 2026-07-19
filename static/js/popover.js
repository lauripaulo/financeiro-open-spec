/* Comportamento do componente popover (details.m3-popover).
 *
 * Campo de data dentro do popover e pre-preenchido com "hoje" no momento da
 * abertura, nao do render — pagina pode ficar aberta alem da meia-noite.
 * O value server-side ({% now %}) permanece como fallback sem JS.
 * toggle nao faz bubble; listener em fase de captura.
 */
(function () {
    document.addEventListener("toggle", function (event) {
        var popover = event.target;
        if (!popover.matches || !popover.matches("details.m3-popover") || !popover.open) {
            return;
        }
        var input = popover.querySelector('input[type="date"]');
        if (input) {
            var hoje = new Date();
            input.value = hoje.getFullYear() + "-"
                + String(hoje.getMonth() + 1).padStart(2, "0") + "-"
                + String(hoje.getDate()).padStart(2, "0");
        }
    }, true);
})();
