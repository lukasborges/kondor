from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QNetworkAccessManager

from kondor.translate.download.bundles import (
    Bundle,
    bundle_tasks,
    file_names,
    total_bytes,
)
from kondor.translate.download.filedownloader import FileDownloader, FileTask
from kondor.translate.storage.translationstore import TranslationStore


class FilesJob(QObject):
    progressed = Signal(int, int)
    finished = Signal(bool)

    def __init__(
        self,
        manager: QNetworkAccessManager,
        store: TranslationStore,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._store = store
        self._downloader = FileDownloader(manager, self)
        self._downloader.progressed.connect(self._on_progress)
        self._downloader.finished.connect(self._on_file_finished)
        self._bundles: list[Bundle] = []
        self._queue: list[tuple[Bundle, FileTask]] = []
        self._base_done = 0
        self._total = 0
        self._is_cancelled = False

    def start(self, bundles: list[Bundle], base_url: str) -> None:
        self._bundles = bundles
        self._total = total_bytes(bundles)
        for bundle in bundles:
            self._store.discard_partial(bundle.directory)
            self._queue += [(bundle, task) for task in bundle_tasks(self._store, base_url, bundle)]
        self._next()

    def cancel(self) -> None:
        self._is_cancelled = True
        self._downloader.cancel()

    def _next(self) -> None:
        if not self._queue:
            self._finish(True)
            return
        self._downloader.start(self._queue[0][1])

    def _on_progress(self, received: int) -> None:
        self.progressed.emit(self._base_done + received, self._total)

    def _on_file_finished(self, ok: bool) -> None:
        bundle, task = self._queue.pop(0)
        if not ok or self._is_cancelled:
            self._finish(False)
            return
        self._base_done += task.size
        self._publish_if_complete(bundle)
        self._next()

    def _publish_if_complete(self, bundle: Bundle) -> None:
        if any(queued is bundle for queued, _ in self._queue):
            return
        self._store.publish(bundle.directory, file_names(bundle))

    def _finish(self, ok: bool) -> None:
        if not ok:
            for bundle in self._bundles:
                self._store.discard_partial(bundle.directory)
        self.finished.emit(ok)
