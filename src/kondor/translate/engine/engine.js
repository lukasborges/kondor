{
    const WORKER_SHIM = "self.ChromeUtils = { addProfilerMarker() {} };\n";
    const IMPORT_LINE = /^importScripts\(.*\);$/m;
    const engines = new Map();
    let api = null;
    let workerUrl = null;
    let sequence = 0;

    const readFile = (url, type) => new Promise((resolve, reject) => {
        const request = new XMLHttpRequest();
        request.open("GET", url);
        request.responseType = type;
        request.onload = () => resolve(request.response);
        request.onerror = () => reject(new Error("Cannot read " + url));
        request.send();
    });

    const buildWorkerUrl = async () => {
        const [glue, worker] = await Promise.all([
            readFile("bergamot-translator.js", "text"),
            readFile("translations-engine.worker.js", "text"),
        ]);
        const source = WORKER_SHIM + glue + "\n" + worker.replace(IMPORT_LINE, "");
        return URL.createObjectURL(new Blob([source], { type: "text/javascript" }));
    };

    const getWorkerUrl = async () => {
        workerUrl = workerUrl || await buildWorkerUrl();
        return workerUrl;
    };

    const readModelFiles = async (files) => {
        const entries = await Promise.all(Object.entries(files).map(async ([kind, file]) => [
            kind, { buffer: await readFile(file.url, "arraybuffer"), record: { name: file.name } },
        ]));
        return Object.fromEntries(entries);
    };

    const readPayload = async (step, wasmUrl) => ({
        bergamotWasmArrayBuffer: await readFile(wasmUrl, "arraybuffer"),
        translationModelPayloads: [{
            sourceLanguage: step.source,
            targetLanguage: step.target,
            languageModelFiles: await readModelFiles(step.files),
        }],
    });

    const settle = (engine, data) => {
        const waiting = engine.pending.get(data.messageId);
        engine.pending.delete(data.messageId);
        if (!waiting)
            return;
        if (data.type === "translation-response")
            waiting.resolve(data.targetText);
        else
            waiting.reject(new Error(data.error && data.error.message));
    };

    const awaitInitialized = (worker) => new Promise((resolve, reject) => {
        worker.onmessage = ({ data }) => {
            if (data.type === "initialization-success")
                resolve();
            else if (data.type === "initialization-error")
                reject(new Error(data.error));
        };
    });

    const createEngine = async (step, wasmUrl) => {
        const worker = new Worker(await getWorkerUrl());
        const initialized = awaitInitialized(worker);
        worker.postMessage({
            type: "initialize", sourceLanguage: step.source, targetLanguage: step.target,
            enginePayload: await readPayload(step, wasmUrl), logLevel: "Error", innerWindowId: 0,
        });
        await initialized;
        const engine = { worker, pending: new Map() };
        worker.onmessage = ({ data }) => settle(engine, data);
        return engine;
    };

    const getEngine = (step, wasmUrl) => {
        const key = step.source + "-" + step.target;
        if (!engines.has(key))
            engines.set(key, createEngine(step, wasmUrl));
        return engines.get(key);
    };

    const request = (engine, text) => new Promise((resolve, reject) => {
        const id = ++sequence;
        engine.pending.set(id, { resolve, reject });
        engine.worker.postMessage({
            type: "translation-request", sourceText: text, messageId: id, translationId: id,
            isHTML: true, innerWindowId: 0,
        });
    });

    const translateStep = async (step, wasmUrl, texts) => {
        const engine = await getEngine(step, wasmUrl);
        return Promise.all(texts.map((text) => request(engine, text)));
    };

    const translateRoute = async (job) => {
        let texts = job.texts;
        for (const step of job.route)
            texts = await translateStep(step, job.wasm, texts);
        return texts;
    };

    const run = async (requestId, source) => {
        try {
            api.deliver(requestId, JSON.stringify(await translateRoute(JSON.parse(source))));
        } catch (error) {
            api.fail(requestId, String(error && error.message));
        }
    };

    const ready = new Promise((resolve) => {
        new QWebChannel(qt.webChannelTransport, (channel) => {
            api = channel.objects.kondorEngine;
            resolve();
        });
    });

    window.kondorTranslate = (requestId, source) => ready.then(() => run(requestId, source));
}
