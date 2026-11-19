from PySide6.QtCore import QObject, Signal

from kondor.translate.download.filesjob import FilesJob


class DownloadTracker(QObject):
    progressChanged = Signal()
    finished = Signal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._progress = (0, 0)
        self._is_cancelling = False

    @property
    def progress(self) -> tuple[int, int]:
        return self._progress

    @property
    def was_cancelled(self) -> bool:
        return self._is_cancelling

    def follow(self, job: FilesJob) -> None:
        self._is_cancelling = False
        job.progressed.connect(self._on_progress)
        job.finished.connect(self._on_finished)

    def cancel(self, jobs: list[FilesJob]) -> None:
        self._is_cancelling = True
        for job in jobs:
            job.cancel()

    def _on_progress(self, done: int, total: int) -> None:
        self._progress = (done, total)
        self.progressChanged.emit()

    def _on_finished(self, ok: bool) -> None:
        self._progress = (0, 0)
        self.progressChanged.emit()
        self.finished.emit(ok)
