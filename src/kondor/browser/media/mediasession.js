{
    const session = navigator.mediaSession;
    const handlers = new Map();

    const announceActions = () => {
        const detail = JSON.stringify(Array.from(handlers.keys()));
        document.dispatchEvent(new CustomEvent("kondor-media-actions", { detail }));
    };

    const rememberHandler = (action, handler) => {
        if (handler)
            handlers.set(action, handler);
        else
            handlers.delete(action);
    };

    const wrapSetActionHandler = () => {
        const original = session.setActionHandler;
        session.setActionHandler = function (action, handler) {
            original.call(session, action, handler);
            rememberHandler(action, handler);
            announceActions();
        };
    };

    const detailsOf = (request) => (request.action === "seekto"
        ? { action: request.action, seekTime: request.seekTime }
        : { action: request.action });

    const callHandler = (request) => {
        const handler = handlers.get(request.action);
        try {
            if (handler)
                handler(detailsOf(request));
        } catch (error) {
            console.debug("Kondor media: the page's action handler failed", error);
        }
    };

    const onActionRequest = (event) => {
        try {
            callHandler(JSON.parse(event.detail));
        } catch (error) {
            console.debug("Kondor media: invalid action request", error);
        }
    };

    if (session) {
        wrapSetActionHandler();
        document.addEventListener("kondor-media-action", onActionRequest);
    }
}
