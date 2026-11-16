{
    const defaultLength = 20;
    const maxLength = 64;
    const minUsefulMaxLength = 8;
    const newFieldName = /new|confirm|repeat|retype|sign.?up|regist|create/i;
    const currentFieldName = /current|old|login|sign.?in/i;

    const isVisible = (el) => el.getClientRects().length > 0 && !el.disabled;

    const isTooShort = (el) => el.maxLength >= 1 && el.maxLength < minUsefulMaxLength;

    const isCandidate = (el) =>
        el instanceof HTMLInputElement && el.type === "password" && isVisible(el) && !isTooShort(el);

    const hasToken = (el, token) =>
        (el.getAttribute("autocomplete") || "").toLowerCase().split(/\s+/).includes(token);

    const scopeOf = (el) => el.form || document;

    const visibleFieldsIn = (scope) =>
        Array.from(scope.querySelectorAll("input[type=password]")).filter(isVisible);

    const unmarkedFieldsIn = (scope) =>
        visibleFieldsIn(scope).filter((el) => !hasToken(el, "current-password"));

    const kindOfSingleField = (el) => {
        const name = el.name + " " + el.id;
        return newFieldName.test(name) && !currentFieldName.test(name) ? "new" : "password";
    };

    const kindAmong = (el, fields) => {
        if (fields.length === 1)
            return kindOfSingleField(el);
        return fields.length >= 3 && fields[0] === el ? "password" : "new";
    };

    const kindOfUnmarked = (el) => {
        const fields = unmarkedFieldsIn(scopeOf(el));
        return fields.includes(el) ? kindAmong(el, fields) : kindOfSingleField(el);
    };

    const kindOf = (el) => {
        if (!isCandidate(el))
            return "";
        if (hasToken(el, "new-password"))
            return "new";
        return hasToken(el, "current-password") ? "password" : kindOfUnmarked(el);
    };

    const confirmationOf = (el) => {
        if (kindOf(el) !== "new")
            return null;
        return visibleFieldsIn(scopeOf(el)).find((other) => other !== el && kindOf(other) === "new") || null;
    };

    const lengthFor = (el) => {
        const raised = Math.min(Math.max(defaultLength, el.minLength), maxLength);
        return el.maxLength > 0 ? Math.min(raised, el.maxLength) : raised;
    };

    const rulesOf = (el) => ({ length: lengthFor(el), useSymbols: true });

    const matchesPattern = (el, value) => {
        const pattern = el.getAttribute("pattern");
        if (!pattern)
            return true;
        try {
            return new RegExp("^(?:" + pattern + ")$", "v").test(value);
        } catch (error) {
            return true;
        }
    };

    window.__kondorNewPasswordFields = { kindOf, confirmationOf, rulesOf, matchesPattern };
}
