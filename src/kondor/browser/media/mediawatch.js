{
    const minimumSeconds = 5;
    const pollMilliseconds = 1000;
    const mediaEvents = ["playing", "pause", "ended", "emptied", "durationchange",
                         "ratechange", "seeked", "loadedmetadata"];
    const stoppedEvents = ["pause", "ended"];
    let bridge = null;
    let active = null;
    let actions = [];
    let lastSnapshot = "";
    let pollTimer = 0;

    const metadata = () => (navigator.mediaSession && navigator.mediaSession.metadata) || {};

    const finiteOrZero = (value) => (Number.isFinite(value) ? value : 0);

    const isEligible = (el) => !el.muted && el.volume > 0
        && (el.duration >= minimumSeconds || el.duration === Infinity);

    const areaOf = (artwork) => {
        const sizes = String(artwork.sizes || "").trim().split(/\s+/);
        const areas = sizes.map((size) => {
            if (size === "any")
                return Infinity;
            const [width, height] = size.split("x").map(Number);
            return width * height || 0;
        });
        return Math.max(0, ...areas);
    };

    const absoluteUrl = (source) => {
        try {
            return new URL(source, location.href).href;
        } catch (error) {
            return "";
        }
    };

    const artworkUrl = () => {
        const list = Array.from(metadata().artwork || []).filter((item) => item && item.src);
        if (list.length === 0)
            return "";
        const best = list.reduce((largest, item) => (areaOf(item) > areaOf(largest) ? item : largest));
        return absoluteUrl(best.src);
    };

    const buildReport = (el, seeked = false) => ({
        hasMedia: true,
        playing: !el.paused,
        title: metadata().title || document.title || location.hostname,
        artist: metadata().artist || location.hostname,
        album: metadata().album || "",
        artworkUrl: artworkUrl(),
        duration: finiteOrZero(el.duration),
        position: finiteOrZero(el.currentTime),
        rate: el.playbackRate,
        actions,
        seeked,
    });

    const snapshotOf = (report) => JSON.stringify(
        [report.title, report.artist, report.album, report.artworkUrl, report.actions]);

    const send = (report) => {
        if (bridge)
            bridge.report(report);
    };

    const reportActive = (seeked = false) => {
        if (!active)
            return;
        const report = buildReport(active, seeked);
        lastSnapshot = snapshotOf(report);
        send(report);
    };

    const forgetActive = () => {
        active = null;
        stopPolling();
        send({ hasMedia: false });
    };

    const pollChanges = () => {
        if (!active || !active.isConnected)
            return forgetActive();
        if (snapshotOf(buildReport(active)) !== lastSnapshot)
            reportActive();
    };

    const startPolling = () => {
        if (!pollTimer)
            pollTimer = setInterval(pollChanges, pollMilliseconds);
    };

    const stopPolling = () => {
        clearInterval(pollTimer);
        pollTimer = 0;
    };

    const adoptIfEligible = (el) => {
        if (el !== active && isEligible(el))
            active = el;
    };

    const updatePolling = (type) => {
        if (stoppedEvents.includes(type))
            stopPolling();
        if (type === "playing")
            startPolling();
    };

    const onMediaEvent = (event) => {
        if (event.type === "playing")
            adoptIfEligible(event.target);
        if (event.target !== active)
            return;
        if (event.type === "emptied")
            return forgetActive();
        updatePolling(event.type);
        reportActive(event.type === "seeked");
    };

    const onActionsAnnounced = (event) => {
        try {
            actions = JSON.parse(event.detail);
        } catch (error) {
            actions = [];
        }
        reportActive();
    };

    const clampedTime = (seconds) => Math.min(Math.max(0, seconds), finiteOrZero(active.duration));

    const defaultAction = (action, seconds) => {
        if (action === "play")
            active.play();
        else if (action === "pause")
            active.pause();
        else if (action === "seekto")
            active.currentTime = clampedTime(seconds);
        else if (action === "stop")
            stopPlayback();
    };

    const stopPlayback = () => {
        active.pause();
        active.currentTime = 0;
    };

    const perform = (action, seconds) => {
        if (!active)
            return;
        if (!actions.includes(action))
            return defaultAction(action, seconds);
        const detail = JSON.stringify({ action, seekTime: seconds });
        document.dispatchEvent(new CustomEvent("kondor-media-action", { detail }));
    };

    const connectBridge = (objects) => {
        bridge = objects.kondorMedia;
        if (!bridge)
            return;
        bridge.actionRequested.connect(perform);
        reportActive();
    };

    const listen = () => {
        mediaEvents.forEach((name) => document.addEventListener(name, onMediaEvent, true));
        document.addEventListener("kondor-media-actions", onActionsAnnounced);
        window.addEventListener("pagehide", () => send({ hasMedia: false }));
    };

    if (window.__kondorChannel) {
        listen();
        window.__kondorChannel.then(connectBridge);
        window.__kondorMediaWatch = { buildReport, setActions: (list) => { actions = list; } };
    }
}
