const ktMaxBatchCharacters = 3000;
const ktMaxBatchUnits = 20;
const ktState = { bridge: null, active: false, applied: [], queue: [], busy: false, requests: new Map(),
    sequence: 0, observer: null, language: "", timer: 0, announced: false };

const ktSend = (action) => { if (ktState.bridge) action(ktState.bridge); };
const ktTopOf = (node) => {
    const element = node.nodeType === 1 ? node : node.parentElement;
    return element ? Math.abs(element.getBoundingClientRect().top) : 0;
};
const ktOrdered = (units) => units.map((unit, index) => ({ unit, index }))
    .sort((a, b) => a.unit.top - b.unit.top || a.index - b.index).map((entry) => entry.unit);

const ktTakeBatch = () => {
    const batch = [];
    let characters = 0;
    while (ktState.queue.length && batch.length < ktMaxBatchUnits && characters < ktMaxBatchCharacters) {
        const unit = ktState.queue.shift();
        characters += unit.html.length;
        batch.push(unit);
    }
    return batch;
};

const ktApplyBatch = (batch, results) => {
    batch.forEach((unit, index) => {
        if (typeof results[index] === "string") {
            unit.apply(results[index]);
            ktState.applied.push(unit);
        }
    });
    if (ktState.observer)
        ktState.observer.takeRecords();
};

const ktAnnounce = () => {
    if (ktState.announced)
        return;
    ktState.announced = true;
    ktSend((bridge) => bridge.reportState("translated"));
};

const ktFinishBatch = (batch, results) => {
    ktState.busy = false;
    if (ktState.active && results) {
        ktApplyBatch(batch, results);
        ktAnnounce();
    } else if (ktState.active) {
        ktSend((bridge) => bridge.reportState("error"));
    }
    ktPump();
};

const ktPump = () => {
    if (ktState.busy || !ktState.active || !ktState.queue.length)
        return;
    ktState.busy = true;
    const batch = ktTakeBatch();
    const id = ++ktState.sequence;
    ktState.requests.set(id, (results) => ktFinishBatch(batch, results));
    ktSend((bridge) => bridge.requestBatch(id, JSON.stringify(batch.map((unit) => unit.html))));
};

const ktEnqueue = (units) => {
    units.forEach((unit) => { unit.top = ktTopOf(unit.node); });
    ktState.queue.push(...ktOrdered(units));
    ktPump();
};

const ktScan = (root) => {
    const units = ktCollect(root);
    ktEnqueue(units);
};

const ktObserve = () => {
    ktState.observer = new MutationObserver((records) => {
        clearTimeout(ktState.timer);
        const added = records.flatMap((record) => Array.from(record.addedNodes));
        ktState.timer = setTimeout(() => added.filter((node) => node.isConnected).forEach(ktScan), 300);
    });
    ktState.observer.observe(document.body, { childList: true, subtree: true });
};

const ktStart = (target) => {
    if (ktState.active || !document.body)
        return;
    ktState.active = true;
    ktState.announced = false;
    ktState.language = document.documentElement.lang;
    document.documentElement.lang = target;
    ktScan(document.body);
    ktObserve();
};

const ktRestore = () => {
    ktState.active = false;
    ktState.queue = [];
    ktState.requests.clear();
    if (ktState.observer)
        ktState.observer.disconnect();
    ktState.applied.forEach((unit) => unit.restore());
    ktState.applied = [];
    document.documentElement.lang = ktState.language;
};

const ktDeliver = (payload) => {
    const { id, results } = JSON.parse(payload);
    const done = ktState.requests.get(id);
    ktState.requests.delete(id);
    if (done)
        done(results);
};

const ktDetectionSample = () => (document.body ? document.body.innerText.slice(0, 2000) : "");

const ktReportLanguage = () => {
    const lang = (document.documentElement.lang || "").trim();
    const known = lang && lang.toLowerCase() !== "und";
    ktSend((bridge) => bridge.reportLanguage(known ? lang : "", known ? "" : ktDetectionSample()));
};

window.__kondorTranslation = { start: ktStart, restore: ktRestore, deliver: ktDeliver };

if (window.__kondorChannel) {
    window.__kondorChannel.then((objects) => {
        ktState.bridge = objects.kondorTranslate;
        if (document.readyState === "complete")
            ktReportLanguage();
    });
    window.addEventListener("load", ktReportLanguage);
}
