if (location.protocol === "devtools:") {
    const message = "kondor:toggle-responsive-mode";

    const isShortcut = (event) =>
        event.ctrlKey && event.shiftKey && !event.altKey && event.code === "KeyM";

    const isDeviceButton = (element) =>
        element.localName === "devtools-button" &&
        (element.previousElementSibling?.getAttribute("jslog") ?? "").includes("toggle-element-search");

    const redirect = (event) => {
        event.preventDefault();
        event.stopImmediatePropagation();
        console.log(message);
    };

    addEventListener("keydown", (event) => {
        if (isShortcut(event))
            redirect(event);
    }, true);

    addEventListener("click", (event) => {
        if (event.composedPath().some(isDeviceButton))
            redirect(event);
    }, true);
}
