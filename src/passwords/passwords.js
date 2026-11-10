// Kondor password manager, page side. Runs in the application world of every
// frame of a normal tab (never in private tabs), after qwebchannel.js, and
// talks to the C++ object "kondorPasswords". The page's own scripts cannot see
// this world or the bridge.
(function () {
    "use strict";

    const origin = location.origin;
    if (!origin || origin === "null" || typeof QWebChannel === "undefined"
            || typeof qt === "undefined" || !qt.webChannelTransport)
        return;

    let bridge = null;
    let requested = false;
    let credentials = [];
    const filled = new WeakSet();
    let lastReport = "";
    let lastReportTime = 0;

    function visible(el) {
        return el.getClientRects().length > 0 && !el.disabled;
    }

    function isTextField(el) {
        const type = (el.getAttribute("type") || "text").toLowerCase();
        return el.tagName === "INPUT" && (type === "text" || type === "email" || type === "tel");
    }

    function passwordFields(scope) {
        return Array.from(scope.querySelectorAll("input[type=password]")).filter(visible);
    }

    // The closest text/email input before the password field.
    function usernameField(password) {
        const scope = password.form || document;
        const inputs = Array.from(scope.querySelectorAll("input"));
        for (let i = inputs.indexOf(password) - 1; i >= 0; i--) {
            if (isTextField(inputs[i]) && visible(inputs[i]))
                return inputs[i];
        }
        return null;
    }

    function setValue(el, value) {
        const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), "value");
        if (setter && setter.set)
            setter.set.call(el, value);
        else
            el.value = value;
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
    }

    // `explicit`: the user picked this account, so replace the username too.
    function fillForm(password, credential, explicit) {
        const user = usernameField(password);
        // Autofill never puts a password next to a different username.
        if (user && !explicit && user.value !== "" && user.value !== credential.username)
            return;
        if (user && user.value !== credential.username)
            setValue(user, credential.username);
        setValue(password, credential.password);
        filled.add(password);
    }

    // Fills every empty password field when exactly one credential is saved.
    function autofill() {
        if (credentials.length !== 1)
            return;
        for (const password of passwordFields(document)) {
            if (!filled.has(password) && password.value === "")
                fillForm(password, credentials[0]);
        }
    }

    function report(scope) {
        if (!bridge)
            return;
        const password = passwordFields(scope).find(function (el) { return el.value !== ""; });
        if (!password)
            return;
        const user = usernameField(password);
        const username = user ? user.value : "";
        // A click on the button and the submit event it causes: report once.
        const key = username + "\u0000" + password.value;
        const now = Date.now();
        if (key === lastReport && now - lastReportTime < 1500)
            return;
        lastReport = key;
        lastReportTime = now;
        bridge.formSubmitted(origin, username, password.value);
    }

    document.addEventListener("submit", function (event) {
        if (event.target instanceof HTMLFormElement)
            report(event.target);
    }, true);

    // Forms driven by JavaScript: a click on a button, outside a <form>, next
    // to a password field.
    document.addEventListener("click", function (event) {
        const target = event.target instanceof Element ? event.target : null;
        const button = target && target.closest("button, input[type=submit], input[type=button], [role=button]");
        if (!button || button.form)
            return;
        for (let node = button.parentElement; node; node = node.parentElement) {
            if (passwordFields(node).length > 0) {
                report(node);
                return;
            }
        }
    }, true);

    // Credentials are requested only once the document has a password field,
    // so a page without one never opens the wallet.
    function loadCredentials() {
        if (passwordFields(document).length === 0) {
            credentials = [];
            return;
        }
        requested = true;
        bridge.credentialsFor(origin, function (list) {
            credentials = Array.isArray(list) ? list : [];
            autofill();
        });
    }

    new QWebChannel(qt.webChannelTransport, function (channel) {
        bridge = channel.objects.kondorPasswords;
        if (!bridge)
            return;
        bridge.credentialsChanged.connect(loadCredentials);
        bridge.fillRequested.connect(function (forOrigin, username, password) {
            if (forOrigin !== origin)
                return;
            const field = passwordFields(document)[0];
            if (field)
                fillForm(field, { username: username, password: password }, true);
        });
        loadCredentials();

        // Login forms that appear later (single-page apps).
        let timer = 0;
        new MutationObserver(function () {
            if (!timer) {
                timer = setTimeout(function () {
                    timer = 0;
                    if (!requested && passwordFields(document).length > 0)
                        loadCredentials();
                    else
                        autofill();
                }, 300);
            }
        }).observe(document.documentElement, { childList: true, subtree: true });
    });
})();
