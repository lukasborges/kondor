// Kondor extension runtime (API version 1), page side. ExtensionManager puts
// this function in front of every content script and calls it with the
// extension's configuration: its id, a per-extension token, a snapshot of its
// settings and the page flags. The returned object is the `kondor` global of
// the extension's scripts; it is only reachable through a closure.
function __kondorCreateRuntime(cfg) {
    "use strict";

    function call(method, args) {
        const channel = window.__kondorChannel;
        if (!channel)
            return Promise.reject(new Error("The Kondor extension bridge is not available"));
        return channel.then(function (objects) {
            const api = objects.kondorExtensions;
            if (!api)
                throw new Error("The Kondor extension bridge is not available");
            return new Promise(function (resolve, reject) {
                api.request(JSON.stringify({id: cfg.id, token: cfg.token, method: method, arguments: args === undefined ? [] : args}),
                            function (reply) {
                    let result;
                    try {
                        result = JSON.parse(reply);
                    } catch (e) {
                        reject(new Error("Invalid reply from Kondor"));
                        return;
                    }
                    if (result.ok)
                        resolve(result.value);
                    else
                        reject(new Error(result.error));
                });
            });
        });
    }

    let values = Object.freeze(Object.assign({}, cfg.settings));
    const settingsListeners = [];
    const actionListeners = [];

    // Called by the browser after the user changed a setting.
    window.__kondorExtensions = window.__kondorExtensions || {};
    window.__kondorExtensions[cfg.id] = function (updated) {
        values = Object.freeze(Object.assign({}, updated));
        settingsListeners.slice().forEach(function (listener) {
            try { listener(values); } catch (e) { console.error(e); }
        });
    };

    // Called by the browser when the user picks a toolbar menu item.
    window.__kondorExtensionActions = window.__kondorExtensionActions || {};
    window.__kondorExtensionActions[cfg.id] = function (itemId, checked) {
        actionListeners.slice().forEach(function (listener) {
            try { listener(itemId, checked); } catch (e) { console.error(e); }
        });
    };

    return Object.freeze({
        extension: Object.freeze({ id: cfg.id, version: cfg.version }),
        locale: cfg.locale,
        isPrivate: cfg.isPrivate,
        settings: Object.freeze({
            get values() { return values; },
            onChanged: function (callback) { settingsListeners.push(callback); }
        }),
        storage: Object.freeze({
            get: function (key) { return call("storage.get", [key]); },
            set: function (key, value) { return call("storage.set", [key, value]); },
            remove: function (key) { return call("storage.remove", [key]); },
            keys: function () { return call("storage.keys"); }
        }),
        onAction: function (callback) { actionListeners.push(callback); },
        action: Object.freeze({
            setChecked: function (itemId, checked) {
                return call("action.setChecked", [itemId, !!checked]);
            }
        }),
        tabs: Object.freeze({
            back: function () { return call("tabs.back"); },
            forward: function () { return call("tabs.forward"); },
            reload: function () { return call("tabs.reload"); },
            close: function () { return call("tabs.close"); },
            open: function (url, options) {
                return call("tabs.open", [String(url), !!(options && options.background)]);
            },
            next: function () { return call("tabs.next"); },
            previous: function () { return call("tabs.previous"); }
        }),
        download: function (url, fileName) {
            return call("download", [String(url), fileName === undefined ? "" : String(fileName)]);
        },
        notify: function (title, body) {
            return call("notify", [String(title), String(body === undefined ? "" : body)]);
        }
    });
}
