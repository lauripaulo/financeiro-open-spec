(function () {
    function wrapWithPrefix(input) {
        if (input.closest(".m3-field--filled")) return;
        var wrapper = document.createElement("span");
        wrapper.className = "m3-field--filled";
        var prefix = document.createElement("span");
        prefix.className = "m3-field__prefix";
        prefix.textContent = "R$";
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(prefix);
        wrapper.appendChild(input);
    }

    function digitsOnly(value) {
        return (value || "").replace(/\D/g, "");
    }

    function formatFromDigits(digits) {
        digits = digits.replace(/^0+(?=\d)/, "");
        while (digits.length < 3) digits = "0" + digits;

        var decimal = digits.slice(-2);
        var inteiro = digits.slice(0, -2) || "0";

        var grupos = [];
        while (inteiro.length > 3) {
            grupos.unshift(inteiro.slice(-3));
            inteiro = inteiro.slice(0, -3);
        }
        grupos.unshift(inteiro);

        return grupos.join(".") + "," + decimal;
    }

    function maskedToPlainDecimal(masked) {
        if (!masked) return "";
        var negative = masked.trim().startsWith("-");
        var digits = digitsOnly(masked);
        if (digits === "") return "";
        while (digits.length < 3) digits = "0" + digits;
        var decimal = digits.slice(-2);
        var inteiro = digits.slice(0, -2).replace(/^0+(?=\d)/, "") || "0";
        return (negative ? "-" : "") + inteiro + "." + decimal;
    }

    function attachMask(input) {
        wrapWithPrefix(input);

        input.addEventListener("input", function () {
            var raw = (input.value || "").trim();
            var negative = raw.startsWith("-");
            var digits = digitsOnly(raw);
            if (digits === "") {
                input.value = negative ? "-" : "";
                return;
            }
            input.value = (negative ? "-" : "") + formatFromDigits(digits);
        });

        var form = input.closest("form");
        if (form) {
            // Capture phase: runs before htmx's own bubble-phase submit
            // listener serializes the form, so hx-post forms send the plain
            // decimal instead of the masked BRL string.
            form.addEventListener("submit", function () {
                input.value = maskedToPlainDecimal(input.value);
            }, true);
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll("input.money-input").forEach(attachMask);
    });
})();
