// ==UserScript==
// @match *://127.0.0.1/*
// @match *://localhost/*
// @exclude *://127.0.0.1:*/excluded/*
// @run-at document-end
// ==/UserScript==
(function () {
const __cfg = {"css":["html[data-kondor-sample] body {\n    border-top: 4px solid #3daee9;\n}\n"],"disabledSites":["https://example.com"],"id":"sample","isPrivate":true,"locale":"en","settings":{"enabledFeature":true,"greeting":"hello","mode":"a","size":50},"token":"@TOKEN@","version":"1.0.0"};
function __kondorBridgeError() {
    return new Error("The Kondor extension bridge is not available");
}

function __kondorParseReply(reply) {
    try {
        return JSON.parse(reply);
    } catch (e) {
        return { ok: false, error: "Invalid reply from Kondor" };
    }
}

function __kondorSettle(reply, resolve, reject) {
    const result = __kondorParseReply(reply);
    if (result.ok)
        resolve(result.value);
    else
        reject(new Error(result.error));
}

function __kondorRequest(api, cfg, request) {
    if (!api)
        throw __kondorBridgeError();
    const payload = JSON.stringify({ id: cfg.id, token: cfg.token, method: request.method,
                                     arguments: request.args === undefined ? [] : request.args });
    return new Promise((resolve, reject) =>
        api.request(payload, (reply) => __kondorSettle(reply, resolve, reject)));
}

function __kondorCall(cfg, method, args) {
    const channel = window.__kondorChannel;
    if (!channel)
        return Promise.reject(__kondorBridgeError());
    return channel.then((objects) =>
        __kondorRequest(objects.kondorExtensions, cfg, { method: method, args: args }));
}

function __kondorNewState(cfg) {
    return {
        values: Object.freeze(Object.assign({}, cfg.settings)),
        settingsListeners: [],
        actionListeners: []
    };
}

function __kondorNotifyAll(listeners, args) {
    listeners.slice().forEach((listener) => {
        try { listener(...args); } catch (e) { console.error(e); }
    });
}

function __kondorRegisterSettingsHook(cfg, state) {
    window.__kondorExtensions = window.__kondorExtensions || {};
    window.__kondorExtensions[cfg.id] = (updated) => {
        state.values = Object.freeze(Object.assign({}, updated));
        __kondorNotifyAll(state.settingsListeners, [state.values]);
    };
}

function __kondorRegisterActionHook(cfg, state) {
    window.__kondorExtensionActions = window.__kondorExtensionActions || {};
    window.__kondorExtensionActions[cfg.id] = (itemId, checked) =>
        __kondorNotifyAll(state.actionListeners, [itemId, checked]);
}

function __kondorIdentityApi(cfg) {
    return {
        extension: Object.freeze({ id: cfg.id, version: cfg.version }),
        locale: cfg.locale,
        isPrivate: cfg.isPrivate
    };
}

function __kondorSettingsApi(state) {
    return Object.freeze({
        get values() { return state.values; },
        onChanged: (callback) => { state.settingsListeners.push(callback); }
    });
}

function __kondorStorageApi(cfg) {
    const call = (method, args) => __kondorCall(cfg, "storage." + method, args);
    return Object.freeze({
        get: (key) => call("get", [key]),
        set: (key, value) => call("set", [key, value]),
        remove: (key) => call("remove", [key]),
        keys: () => call("keys")
    });
}

function __kondorActionApi(cfg) {
    return Object.freeze({
        setChecked: (itemId, checked) =>
            __kondorCall(cfg, "action.setChecked", [itemId, !!checked])
    });
}

function __kondorTabsApi(cfg) {
    const call = (method, args) => __kondorCall(cfg, "tabs." + method, args);
    const open = (url, options) => call("open", [String(url), !!(options && options.background)]);
    return Object.freeze({
        back: () => call("back"), forward: () => call("forward"),
        reload: () => call("reload"), close: () => call("close"),
        open: open, next: () => call("next"), previous: () => call("previous")
    });
}

function __kondorMessagingApi(cfg) {
    return {
        download: (url, fileName) => __kondorCall(cfg, "download",
            [String(url), fileName === undefined ? "" : String(fileName)]),
        notify: (title, body) => __kondorCall(cfg, "notify",
            [String(title), String(body === undefined ? "" : body)])
    };
}

function __kondorOwnApis(cfg, state) {
    return {
        settings: __kondorSettingsApi(state),
        storage: __kondorStorageApi(cfg),
        onAction: (callback) => { state.actionListeners.push(callback); },
        action: __kondorActionApi(cfg),
        tabs: __kondorTabsApi(cfg)
    };
}

function __kondorCreateRuntime(cfg) {
    const state = __kondorNewState(cfg);
    __kondorRegisterSettingsHook(cfg, state);
    __kondorRegisterActionHook(cfg, state);
    return Object.freeze(Object.assign({}, __kondorIdentityApi(cfg),
                                       __kondorOwnApis(cfg, state), __kondorMessagingApi(cfg)));
}

if (__cfg.disabledSites.indexOf(location.origin) !== -1)
    return;
const kondor = __kondorCreateRuntime(__cfg);
(function (styles) {
    if (styles.length === 0) return;
    function add() {
        styles.forEach(function (text) {
            const style = document.createElement("style");
            style.textContent = text;
            document.documentElement.appendChild(style);
        });
    }
    if (document.documentElement) { add(); return; }
    new MutationObserver(function (records, observer) {
        if (document.documentElement) { observer.disconnect(); add(); }
    }).observe(document, { childList: true });
})(__cfg.css);
(function (kondor) {
// Marks the page so the tests (and the manual test) can see it ran.
const root = document.documentElement;
root.setAttribute("data-kondor-sample", kondor.settings.values.greeting);
root.setAttribute("data-kondor-private", String(kondor.isPrivate));

kondor.settings.onChanged(function (values) {
    root.setAttribute("data-kondor-sample", values.greeting);
});

kondor.onAction(function (itemId, checked) {
    root.setAttribute("data-kondor-action", itemId + ":" + checked);
});

kondor.storage.set("lastGreeting", kondor.settings.values.greeting).then(function () {
    root.setAttribute("data-kondor-storage", "ok");
}, function (error) {
    root.setAttribute("data-kondor-storage", error.message);
});

;
})(kondor);
})();
