import time
import weakref
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import ClassVar

from PySide6.QtCore import QObject, QUrl, Slot

from kondor.app.crash.navigationkind import navigation_kind

MAX_ENTRIES = 40


def clock_text() -> str:
    return time.strftime("%H:%M:%S")


class ActionLog(QObject):
    _instance: ClassVar["ActionLog | None"] = None

    def __init__(self, clock: Callable[[], str] = clock_text) -> None:
        super().__init__()
        self._clock = clock
        self._path: Path | None = None
        self._entries: deque[str] = deque(maxlen=MAX_ENTRIES)
        self._previous_urls: weakref.WeakKeyDictionary[QObject, QUrl] = (
            weakref.WeakKeyDictionary()
        )

    @classmethod
    def instance(cls) -> "ActionLog":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start(self, path: Path) -> None:
        self._path = path
        self._entries.clear()
        self._previous_urls.clear()
        self._write()

    def stop(self) -> None:
        self._path = None

    def record(self, event: str) -> None:
        if self._path is None:
            return
        self._entries.append(f"{self._clock()} {event}")
        self._write()

    def record_unless_private(self, is_private: bool, event: str) -> None:
        if not is_private:
            self.record(event)

    def record_tab(self, tab: QObject, event: str) -> None:
        self.record_unless_private(bool(tab.property("isPrivate")), event)

    def _write(self) -> None:
        if self._path is None:
            return
        try:
            self._path.write_text(
                "".join(f"{entry}\n" for entry in self._entries), encoding="utf-8"
            )
        except OSError:
            self._path = None

    @Slot(QObject, str)
    def pageEvent(self, tab: QObject, event: str) -> None:
        self.record_tab(tab, event)

    @Slot(QObject, QUrl)
    def navigationStarted(self, tab: QObject, url: QUrl) -> None:
        if bool(tab.property("isPrivate")):
            return
        kind = navigation_kind(self._previous_urls.get(tab, QUrl()), url)
        self._previous_urls[tab] = url
        self.record(f"navigation started {kind}")

    @Slot(QObject)
    def navigationFinished(self, tab: QObject) -> None:
        self.record_tab(tab, "navigation finished")

    @Slot(QObject, int)
    def navigationFailed(self, tab: QObject, error_code: int) -> None:
        self.record_tab(tab, f"navigation failed error {error_code}")
