const __gmInfo = Object.freeze({
    script: Object.freeze({
        name: __userScript.name,
        namespace: __userScript.namespace,
        version: __userScript.version,
        description: __userScript.description
    }),
    scriptHandler: "Kondor",
    version: __userScript.kondorVersion
});

function __gmGetValue(key, defaultValue) {
    return kondor.storage.get(key).then(
        (value) => (value === undefined || value === null) ? defaultValue : value);
}

function __gmWhenRootExists(callback) {
    new MutationObserver((records, observer) => {
        if (!document.documentElement)
            return;
        observer.disconnect();
        callback();
    }).observe(document, { childList: true });
}

function __gmAttachStyle(style) {
    const parent = document.head || document.documentElement;
    if (parent)
        parent.appendChild(style);
    else
        __gmWhenRootExists(() => __gmAttachStyle(style));
}

function __gmAddStyle(css) {
    const style = document.createElement("style");
    style.textContent = css;
    __gmAttachStyle(style);
    return style;
}

function __gmNotificationOptions(first, second) {
    if (typeof first === "object" && first !== null)
        return first;
    return { text: first, title: second };
}

function __gmNotification(first, second) {
    const options = __gmNotificationOptions(first, second);
    return kondor.notify(options.title || __userScript.name,
                         options.text === undefined ? "" : options.text);
}

const GM = Object.freeze({
    info: __gmInfo,
    getValue: __gmGetValue,
    setValue: (key, value) => kondor.storage.set(key, value),
    deleteValue: (key) => kondor.storage.remove(key),
    listValues: () => kondor.storage.keys(),
    addStyle: __gmAddStyle,
    notification: __gmNotification
});

const GM_info = __gmInfo;
const GM_addStyle = __gmAddStyle;
const GM_notification = __gmNotification;
