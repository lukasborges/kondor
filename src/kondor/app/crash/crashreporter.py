from typing import ClassVar

from PySide6.QtCore import QObject, QUrl, Slot
from PySide6.QtGui import QGuiApplication

from kondor.app.crash.crashfiles import CrashFiles
from kondor.app.crash.crashreport import CrashReport


class CrashReporter(QObject):
    _instance: ClassVar["CrashReporter | None"] = None

    def __init__(self) -> None:
        super().__init__()
        self._files: CrashFiles | None = None
        self._is_claimed = False

    @classmethod
    def instance(cls) -> "CrashReporter":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def offer(self, files: CrashFiles) -> None:
        self._files = files
        self._is_claimed = False

    @Slot(result=bool)
    def claimBar(self) -> bool:
        if self._files is None or self._is_claimed or not self._files.has_previous_crash():
            return False
        self._is_claimed = True
        return True

    @Slot(result=QUrl)
    def report(self) -> QUrl:
        if self._files is None:
            return QUrl()
        report = self.read_report(self._files)
        if report.is_too_long():
            QGuiApplication.clipboard().setText(report.body())
        self.dismiss()
        return QUrl(report.address())

    @Slot()
    def dismiss(self) -> None:
        if self._files is not None:
            self._files.discard_previous_crash()

    @staticmethod
    def read_report(files: CrashFiles) -> CrashReport:
        return CrashReport(
            files.read_previous_crash(),
            files.read_previous_actions(),
            str(QGuiApplication.applicationVersion()),
        )
