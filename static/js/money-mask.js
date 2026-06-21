(function () {
    function wrapWithPrefix(input) {
        if (input.closest(".money-field")) return;
        var wrapper = document.createElement("span");
        wrapper.className = "money-field";
        var prefix = document.createElement("span");
        prefix.className = "money-prefix";
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
        var cleaned = masked.replace(/\./g, "").replace(",", ".");
        var parsed = parseFloat(cleaned);
        return isNaN(parsed) ? "" : parsed.toFixed(2);
    }

    function attachMask(input) {
        wrapWithPrefix(input);

        input.addEventListener("input", function () {
            var digits = digitsOnly(input.value);
            input.value = digits === "" ? "" : formatFromDigits(digits);
        });

        var form = input.closest("form");
        if (form) {
            form.addEventListener("submit", function () {
                input.value = maskedToPlainDecimal(input.value);
            });
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll("input.money-input").forEach(attachMask);
    });
})();
