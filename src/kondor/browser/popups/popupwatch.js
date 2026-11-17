{
    let bridge = null;
    const pending = [];

    const send = (url) => {
        if (bridge)
            bridge.reportBlocked(url);
        else
            pending.push(url);
    };

    const onBlocked = (event) => {
        try {
            send(JSON.parse(event.detail).url);
        } catch (error) {
            return;
        }
    };

    const connectBridge = (objects) => {
        bridge = objects.kondorPopups;
        if (bridge)
            pending.splice(0).forEach(send);
    };

    if (window.__kondorChannel) {
        document.addEventListener("kondor-popup-blocked", onBlocked);
        window.__kondorChannel.then(connectBridge);
    }
}
