import json
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

from PySide6.QtCore import QObject, QTimer, QUrl, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile

from kondor.translate.engine.enginepage import write_page
from kondor.translate.storage.translationstore import TranslationStore

IDLE_MILLISECONDS = 5 * 60 * 1000
CHANNEL_OBJECT = "kondorEngine"
DoneCallback = Callable[[list[str]], None]
FailCallback = Callable[[str], None]


class Step(NamedTuple):
    source: str
    target: str
    files: dict[str, Path]


class EngineJob(NamedTuple):
    steps: list[Step]
    texts: list[str]


class Pending(NamedTuple):
    done: DoneCallback
    fail: FailCallback


def step_payload(step: Step) -> dict[str, object]:
    files = {
        kind: {"url": QUrl.fromLocalFile(str(path)).toString(), "name": path.name}
        for kind, path in step.files.items()
    }
    return {"source": step.source, "target": step.target, "files": files}


def job_source(job: EngineJob, wasm: Path) -> str:
    wasm_url = QUrl.fromLocalFile(str(wasm)).toString()
    route = [step_payload(step) for step in job.steps]
    return json.dumps({"route": route, "wasm": wasm_url, "texts": job.texts})


class EnginePageApi(QObject):
    def __init__(self, engine: "TranslationEngine") -> None:
        super().__init__(engine)
        self._engine = engine

    @Slot(str, str)
    def deliver(self, request_id: str, results: str) -> None:
        self._engine.receive_results(request_id, results)

    @Slot(str, str)
    def fail(self, request_id: str, message: str) -> None:
        self._engine.receive_failure(request_id, message)


class TranslationEngine(QObject):
    def __init__(self, store: TranslationStore, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._store = store
        self._page: QWebEnginePage | None = None
        self._profile: QWebEngineProfile | None = None
        self._is_loaded = False
        self._queued: list[str] = []
        self._pending: dict[str, Pending] = {}
        self._sequence = 0
        self._idle = self._make_idle_timer()

    def _make_idle_timer(self) -> QTimer:
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(IDLE_MILLISECONDS)
        timer.timeout.connect(self.close)
        return timer

    def translate(self, job: EngineJob, done: DoneCallback, fail: FailCallback) -> None:
        if not self._ensure_page():
            fail("The translation engine is not available")
            return
        self._sequence += 1
        request_id = str(self._sequence)
        self._pending[request_id] = Pending(done, fail)
        source = job_source(job, self._store.engine_path)
        self._run(f"kondorTranslate({json.dumps(request_id)}, {json.dumps(source)});")
        self._idle.start()

    def receive_results(self, request_id: str, results: str) -> None:
        pending = self._pending.pop(request_id, None)
        if pending is not None:
            pending.done(json.loads(results))

    def receive_failure(self, request_id: str, message: str) -> None:
        pending = self._pending.pop(request_id, None)
        if pending is not None:
            pending.fail(message)

    @Slot()
    def close(self) -> None:
        for pending in self._pending.values():
            pending.fail("The translation engine closed")
        self._pending.clear()
        self._is_loaded = False
        self._queued.clear()
        if self._page is not None:
            self._page.deleteLater()
            self._page = None

    def _run(self, script: str) -> None:
        if self._page is None:
            return
        if self._is_loaded:
            self._page.runJavaScript(script)
        else:
            self._queued.append(script)

    def _ensure_page(self) -> bool:
        if self._page is not None:
            return True
        entry = write_page(self._store.page_directory)
        if entry is None:
            return False
        self._profile = self._profile or QWebEngineProfile(self)
        self._page = self._make_page(self._profile)
        self._page.load(QUrl.fromLocalFile(str(entry)))
        return True

    def _make_page(self, profile: QWebEngineProfile) -> QWebEnginePage:
        page = QWebEnginePage(profile, self)
        channel = QWebChannel(page)
        channel.registerObject(CHANNEL_OBJECT, EnginePageApi(self))
        page.setWebChannel(channel)
        page.loadFinished.connect(self._on_loaded)
        return page

    def _on_loaded(self, ok: bool) -> None:
        if not ok or self._page is None:
            self.close()
            return
        self._is_loaded = True
        for script in self._queued:
            self._page.runJavaScript(script)
        self._queued.clear()
