{
    const originalOpen = window.open;
    const hasUserActivation = () => Boolean(
        navigator.userActivation && navigator.userActivation.isActive);
    const isDetached = (features) => /noopener/i.test(String(features || ""));
    const absoluteUrl = (source) => {
        try {
            return new URL(source || "about:blank", location.href).href;
        } catch (error) {
            return "";
        }
    };
    const reportBlocked = (source) => {
        const detail = JSON.stringify({ url: absoluteUrl(source) });
        document.dispatchEvent(new CustomEvent("kondor-popup-blocked", { detail }));
    };
    const guardedOpen = function (source, target, features) {
        const hadActivation = hasUserActivation();
        const opened = originalOpen.apply(this, arguments);
        if (opened === null && !hadActivation && !isDetached(features))
            reportBlocked(source);
        return opened;
    };
    Object.defineProperty(guardedOpen, "name", { value: "open" });
    window.open = guardedOpen;
}
