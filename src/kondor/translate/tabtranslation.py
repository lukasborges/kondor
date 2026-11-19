import json

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from kondor.translate import languagelists
from kondor.translate.downloadtracker import DownloadTracker
from kondor.translate.page.languagedetect import page_language
from kondor.translate.service import BatchRequest, TranslationService
from kondor.translate.storage.translationstore import Pair
from kondor.translate.tablists import TabTranslationLists
from kondor.translate.translationflow import (
    BUSY_STATES,
    PAGE_STATE_ERROR,
    PAGE_STATE_TRANSLATED,
    STATE_DOWNLOADING,
    STATE_ERROR,
    STATE_IDLE,
    STATE_TRANSLATED,
    STATE_TRANSLATING,
    is_offerable,
    megabytes,
    pair_label,
    progress_fraction,
    web_host,
)


class TabTranslation(QObject):
    stateChanged = Signal()
    availableChanged = Signal()
    languagesChanged = Signal()
    progressChanged = Signal()
    actionRequested = Signal(str, str)

    def __init__(self, is_private: bool, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._service = TranslationService.instance()
        self._lists = TabTranslationLists(is_private, self)
        self._tracker = DownloadTracker(self)
        self._tracker.progressChanged.connect(self.progressChanged)
        self._tracker.finished.connect(self._on_downloaded)
        self._lists.changed.connect(self._refresh_available)
        self._init_state()

    def _init_state(self) -> None:
        self._state = STATE_IDLE
        self._is_available = False
        self._detected = self._source = ""
        self._target = languagelists.target_language()
        self._generation = 0

    state = Property(str, lambda self: self._state, notify=stateChanged)
    isAvailable = Property(bool, lambda self: self._is_available, notify=availableChanged)
    lists = Property(TabTranslationLists, lambda self: self._lists, constant=True)
    detectedLanguage = Property(str, lambda self: self._detected, notify=languagesChanged)
    sourceLanguage = Property(str, lambda self: self._source, notify=languagesChanged)
    targetLanguage = Property(str, lambda self: self._target, notify=languagesChanged)
    downloadedMegabytes = Property(
        int, lambda self: megabytes(self._tracker.progress[0]), notify=progressChanged
    )
    totalMegabytes = Property(
        int, lambda self: megabytes(self._tracker.progress[1]), notify=progressChanged
    )
    progress = Property(
        float, lambda self: progress_fraction(*self._tracker.progress), notify=progressChanged
    )
    downloadLabel = Property(
        str, lambda self: pair_label(self._source, self._target), notify=languagesChanged
    )

    sourceCodes = Property(
        "QStringList", lambda self: self._service.source_codes(), notify=languagesChanged
    )
    targetCodes = Property(
        "QStringList", lambda self: self._service.target_codes(), notify=languagesChanged
    )

    def update_for(self, url: QUrl) -> None:
        self._lists.set_host(web_host(url))

    def reset(self) -> None:
        self._generation += 1
        self._detected = self._source = ""
        self._target = languagelists.target_language()
        if self._state != STATE_DOWNLOADING:
            self._set_state(STATE_IDLE)
        self._lists.set_language("")
        self.languagesChanged.emit()

    def receive_language(self, declared: str, sample: str) -> None:
        language = page_language(declared, sample)
        if language is None or language == self._detected:
            return
        self._detected = self._source = language
        self._lists.set_language(language)
        self.languagesChanged.emit()
        generation = self._generation
        self._service.ensure_catalog(lambda _ok: self._on_catalog(generation))

    def receive_batch(self, batch_id: int, texts_json: str) -> None:
        route = self._service.route(self._source, self._target)
        if route is None or self._state not in (STATE_TRANSLATING, STATE_TRANSLATED):
            return
        request = BatchRequest(route, json.loads(texts_json))
        self._service.translate(
            request,
            lambda results: self._deliver(batch_id, results),
            lambda _message: self._deliver(batch_id, None),
        )

    def receive_state(self, state: str) -> None:
        if state == PAGE_STATE_TRANSLATED and self._state == STATE_TRANSLATING:
            self._set_state(STATE_TRANSLATED)
        elif state == PAGE_STATE_ERROR and self._state != STATE_IDLE:
            self._set_state(STATE_ERROR)

    @Slot()
    def translate(self) -> None:
        if self._state in BUSY_STATES:
            return
        route = self._service.route(self._source, self._target)
        if route is None:
            self._set_state(STATE_ERROR)
        else:
            self._start(route)

    def _start(self, route: list[Pair]) -> None:
        job = self._service.download(route)
        if job is None:
            self._begin()
            return
        self._set_state(STATE_DOWNLOADING)
        self._tracker.follow(job)

    @Slot()
    def cancel(self) -> None:
        self._tracker.cancel()

    @Slot()
    def showOriginal(self) -> None:
        self.actionRequested.emit("restore", "")
        self._set_state(STATE_IDLE)

    @Slot(str)
    def setSourceLanguage(self, code: str) -> None:
        self._source = code
        self._after_language_change()

    @Slot(str)
    def setTargetLanguage(self, code: str) -> None:
        self._target = code
        self._after_language_change()

    def _after_language_change(self) -> None:
        self.languagesChanged.emit()
        if self._state in (STATE_TRANSLATED, STATE_TRANSLATING):
            self.showOriginal()
            self.translate()

    def _on_downloaded(self, ok: bool) -> None:
        if self._tracker.was_cancelled:
            self._set_state(STATE_IDLE)
        elif ok:
            self._begin()
        else:
            self._set_state(STATE_ERROR)

    def _begin(self) -> None:
        self._set_state(STATE_TRANSLATING)
        self.actionRequested.emit("start", self._target)

    def _deliver(self, batch_id: int, results: list[str] | None) -> None:
        self.actionRequested.emit("deliver", json.dumps({"id": batch_id, "results": results}))

    def _on_catalog(self, generation: int) -> None:
        if generation != self._generation:
            return
        self.languagesChanged.emit()
        self._refresh_available()
        if self._is_available and self._lists.is_always():
            self.translate()

    def _refresh_available(self) -> None:
        supported = self._service.is_offered(self._detected, self._target)
        allowed = supported and not self._lists.is_blocked()
        available = is_offerable(self._detected, self._target, allowed) or self._state != STATE_IDLE
        if available != self._is_available:
            self._is_available = available
            self.availableChanged.emit()

    def _set_state(self, state: str) -> None:
        if state == self._state:
            return
        self._state = state
        self.stateChanged.emit()
        self._refresh_available()
