{
    const origin = location.origin;
    const scrollGraceMs = 400;
    const dismissed = new WeakSet();
    const fields = window.__kondorNewPasswordFields;
    let bridge = null;
    let current = null;
    let isOffered = false;
    let focusedAt = 0;

    const isOfferable = (field, kind) => kind === "new" && field.value === "" && !dismissed.has(field);

    const describe = (field, kind) => {
        const rect = field.getBoundingClientRect();
        return {
            kind: kind,
            offer: isOffered,
            x: rect.x,
            y: rect.y,
            width: rect.width,
            height: rect.height
        };
    };

    const rememberFocus = (field, kind) => {
        current = field;
        isOffered = isOfferable(field, kind);
        focusedAt = Date.now();
    };

    const onFocusIn = (event) => {
        const kind = fields.kindOf(event.target);
        if (!kind)
            return;
        rememberFocus(event.target, kind);
        bridge.passwordFieldFocused(describe(event.target, kind));
    };

    const withdraw = () => {
        if (!current || !isOffered)
            return;
        dismissed.add(current);
        isOffered = false;
        bridge.passwordFieldFocused(describe(current, fields.kindOf(current)));
    };

    const leave = () => {
        if (!current)
            return;
        withdraw();
        current = null;
        bridge.passwordFieldLeft();
    };

    const onFocusOut = (event) => {
        if (event.target === current && document.hasFocus())
            leave();
    };

    const onInput = (event) => {
        if (event.target === current)
            withdraw();
    };

    const onKeyDown = (event) => {
        if (event.key === "Escape" && event.target === current)
            withdraw();
    };

    const onMove = () => {
        if (Date.now() - focusedAt > scrollGraceMs)
            withdraw();
    };

    const candidateRules = (field) => {
        const rules = fields.rulesOf(field);
        return [rules, { ...rules, useSymbols: false }, { ...rules, useSymbols: false }];
    };

    const fillGenerated = (field, value) => {
        const confirmation = fields.confirmationOf(field);
        dismissed.add(field);
        window.__kondorSetFieldValue(field, value);
        if (confirmation)
            window.__kondorSetFieldValue(confirmation, value);
        bridge.generatedPasswordFilled(origin, value);
        current = null;
        bridge.passwordFieldLeft();
    };

    const generateFor = (field, pendingRules) => {
        if (pendingRules.length === 0)
            return;
        bridge.generatePassword(pendingRules[0], (value) => {
            if (value && fields.matchesPattern(field, value))
                fillGenerated(field, value);
            else
                generateFor(field, pendingRules.slice(1));
        });
    };

    const generateForCurrent = () => {
        if (current)
            generateFor(current, candidateRules(current));
    };

    const watchPage = () => {
        document.addEventListener("focusin", onFocusIn, true);
        document.addEventListener("focusout", onFocusOut, true);
        document.addEventListener("input", onInput, true);
        document.addEventListener("keydown", onKeyDown, true);
        window.addEventListener("scroll", onMove);
        window.addEventListener("resize", onMove);
    };

    const connectBridge = (objects) => {
        bridge = objects.kondorPasswords;
        if (!bridge)
            return;
        bridge.generateRequested.connect(generateForCurrent);
        watchPage();
    };

    if (origin && origin !== "null" && window.__kondorChannel)
        window.__kondorChannel.then(connectBridge);
}
