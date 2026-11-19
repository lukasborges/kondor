from collections.abc import Callable

from PySide6.QtCore import Property, QObject, Signal, Slot

from kondor.translate import languagelists
from kondor.translate.languagenames import language_name


class TabTranslationLists(QObject):
    changed = Signal()

    def __init__(self, is_private: bool, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._is_private = is_private
        self._language = ""
        self._host = ""

    canChange = Property(bool, lambda self: not self._is_private, constant=True)
    host = Property(str, lambda self: self._host, notify=changed)
    languageName = Property(str, lambda self: language_name(self._language), notify=changed)
    isAlways = Property(bool, lambda self: self._is_listed(languagelists.ALWAYS), notify=changed)
    isNever = Property(bool, lambda self: self._is_listed(languagelists.NEVER), notify=changed)
    isNeverHost = Property(bool, lambda self: self._is_host_listed(), notify=changed)

    def set_language(self, language: str) -> None:
        self._language = language
        self.changed.emit()

    def set_host(self, host: str) -> None:
        if host != self._host:
            self._host = host
            self.changed.emit()

    def is_blocked(self) -> bool:
        return self._is_listed(languagelists.NEVER) or self._is_host_listed()

    def is_always(self) -> bool:
        return self._is_listed(languagelists.ALWAYS)

    @Slot(bool)
    def setAlways(self, enabled: bool) -> None:
        self._write(lambda: languagelists.set_always(self._language, enabled))

    @Slot(bool)
    def setNever(self, enabled: bool) -> None:
        self._write(lambda: languagelists.set_never(self._language, enabled))

    @Slot(bool)
    def setNeverHost(self, enabled: bool) -> None:
        self._write(
            lambda: languagelists.set_listed(languagelists.NEVER_HOSTS, self._host, enabled)
        )

    def _is_listed(self, name: str) -> bool:
        return bool(self._language) and languagelists.is_listed(name, self._language)

    def _is_host_listed(self) -> bool:
        return bool(self._host) and languagelists.is_listed(languagelists.NEVER_HOSTS, self._host)

    def _write(self, change: Callable[[], None]) -> None:
        if self._is_private:
            return
        change()
        self.changed.emit()
