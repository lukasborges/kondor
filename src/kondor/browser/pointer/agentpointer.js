{
    const reportedEvents = ["pointermove", "pointerdown"];
    let bridge = null;
    let pendingMove = null;
    let isMoveScheduled = false;

    const send = (type, x, y) => {
        if (bridge)
            bridge.report(type, x, y);
    };

    const flushMove = () => {
        isMoveScheduled = false;
        if (pendingMove)
            send("pointermove", pendingMove.x, pendingMove.y);
        pendingMove = null;
    };

    const queueMove = (event) => {
        pendingMove = { x: event.clientX, y: event.clientY };
        if (isMoveScheduled)
            return;
        isMoveScheduled = true;
        requestAnimationFrame(flushMove);
    };

    const onPointerEvent = (event) => {
        if (!event.isTrusted)
            return;
        if (event.type === "pointermove")
            queueMove(event);
        else
            send(event.type, event.clientX, event.clientY);
    };

    const connectBridge = (objects) => {
        bridge = objects.kondorAgentPointer;
    };

    if (window.__kondorChannel) {
        reportedEvents.forEach((name) => window.addEventListener(name, onPointerEvent, true));
        window.__kondorChannel.then(connectBridge);
    }
}
