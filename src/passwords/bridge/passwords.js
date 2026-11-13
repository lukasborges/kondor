{
    const origin = location.origin;
    const duplicateReportWindowMs = 1500;
    const refreshDelayMs = 300;
    const filled = new WeakSet();
    let bridge = null;
    let requested = false;
    let credentials = [];
    let lastReport = "";
    let lastReportTime = 0;
    let refreshTimer = 0;

    const isVisible = (el) => el.getClientRects().length > 0 && !el.disabled;

    const isTextField = (el) => {
        const type = (el.getAttribute("type") || "text").toLowerCase();
        return el.tagName === "INPUT" && (type === "text" || type === "email" || type === "tel");
    };

    const passwordFields = (scope) =>
        Array.from(scope.querySelectorAll("input[type=password]")).filter(isVisible);

    const visibleTextFields = () => Array.from(document.querySelectorAll("input")).filter((el) => isTextField(el) && isVisible(el));

    const hasLoginField = () =>
        passwordFields(document).length > 0
            || !!window.__kondorPickUsernameField(visibleTextFields());

    const inputsBefore = (password) => {
        const scope = password.form || document;
        const inputs = Array.from(scope.querySelectorAll("input"));
        const index = inputs.indexOf(password);
        return index < 0 ? [] : inputs.slice(0, index).reverse();
    };

    const usernameField = (password) =>
        inputsBefore(password).find((el) => isTextField(el) && isVisible(el)) || null;

    const nativeValueDescriptor = (el) =>
        Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), "value");

    const dispatchValueEvents = (el) => {
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
    };

    const setValue = (el, value) => {
        const descriptor = nativeValueDescriptor(el);
        if (descriptor && descriptor.set)
            descriptor.set.call(el, value);
        else
            el.value = value;
        dispatchValueEvents(el);
    };

    const hasOtherUsername = (user, credential) =>
        !!user && user.value !== "" && user.value !== credential.username;

    const fillForm = (password, credential, explicit) => {
        const user = usernameField(password);
        if (!explicit && hasOtherUsername(user, credential))
            return;
        if (user && user.value !== credential.username)
            setValue(user, credential.username);
        setValue(password, credential.password);
        filled.add(password);
    };

    const needsAutofill = (password) => !filled.has(password) && password.value === "";

    const autofill = () => {
        if (credentials.length !== 1)
            return;
        passwordFields(document).filter(needsAutofill)
            .forEach((password) => fillForm(password, credentials[0]));
    };

    const reportableLogin = (scope) => {
        const password = passwordFields(scope).find((el) => el.value !== "");
        if (!password)
            return null;
        const user = usernameField(password);
        return { username: user ? user.value : "", password: password.value };
    };

    const reportKey = (login) => login.username + "\u0000" + login.password;

    const isDuplicateReport = (login) =>
        reportKey(login) === lastReport && Date.now() - lastReportTime < duplicateReportWindowMs;

    const rememberReport = (login) => {
        lastReport = reportKey(login);
        lastReportTime = Date.now();
    };

    const report = (scope) => {
        const login = bridge && reportableLogin(scope);
        if (!login || isDuplicateReport(login))
            return;
        rememberReport(login);
        bridge.formSubmitted(origin, login.username, login.password);
    };

    const reportSubmittedForm = (event) => {
        if (event.target instanceof HTMLFormElement)
            report(event.target);
    };

    const clickedButton = (event) => {
        const target = event.target instanceof Element ? event.target : null;
        return target && target.closest("button, input[type=submit], input[type=button], [role=button]");
    };

    const enclosingPasswordScope = (button) => {
        for (let node = button.parentElement; node; node = node.parentElement) {
            if (passwordFields(node).length > 0)
                return node;
        }
        return null;
    };

    const reportClickedButton = (event) => {
        const button = clickedButton(event);
        if (!button || button.form)
            return;
        const scope = enclosingPasswordScope(button);
        if (scope)
            report(scope);
    };

    const applyCredentials = (list) => {
        credentials = Array.isArray(list) ? list : [];
        autofill();
    };

    const loadCredentials = () => {
        if (!hasLoginField()) {
            credentials = [];
            return;
        }
        requested = true;
        bridge.credentialsFor(origin, applyCredentials);
    };

    const fillUsernameOnly = (username) => {
        const field = window.__kondorPickUsernameField(visibleTextFields());
        if (field)
            setValue(field, username);
    };

    const fillFirstField = (forOrigin, username, password) => {
        if (forOrigin !== origin)
            return;
        const field = passwordFields(document)[0];
        if (field)
            fillForm(field, { username: username, password: password }, true);
        else
            fillUsernameOnly(username);
    };

    const refreshAfterMutation = () => (requested ? autofill() : loadCredentials());

    const runScheduledRefresh = () => {
        refreshTimer = 0;
        refreshAfterMutation();
    };

    const scheduleRefresh = () => {
        if (!refreshTimer)
            refreshTimer = setTimeout(runScheduledRefresh, refreshDelayMs);
    };

    const observeLaterForms = () => {
        new MutationObserver(scheduleRefresh)
            .observe(document.documentElement, { childList: true, subtree: true });
    };

    const connectBridge = (objects) => {
        bridge = objects.kondorPasswords;
        if (!bridge)
            return;
        bridge.credentialsChanged.connect(loadCredentials);
        bridge.fillRequested.connect(fillFirstField);
        loadCredentials();
        observeLaterForms();
    };

    const hasUsableOrigin = () => !!origin && origin !== "null" && !!window.__kondorChannel;

    const startAutofill = () => {
        if (!hasUsableOrigin())
            return;
        document.addEventListener("submit", reportSubmittedForm, true);
        document.addEventListener("click", reportClickedButton, true);
        window.__kondorChannel.then(connectBridge);
    };

    startAutofill();
}
