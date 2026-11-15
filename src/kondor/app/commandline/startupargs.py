from typing import ClassVar

from PySide6.QtCore import Property, QObject, QUrl


class StartupArgs(QObject):
    _instance: ClassVar["StartupArgs | None"] = None

    def __init__(self) -> None:
        super().__init__()
        self._startup_urls: list[QUrl] = []
        self._startup_private = False

    @classmethod
    def instance(cls) -> "StartupArgs":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_startup_urls(self, urls: list[QUrl]) -> None:
        self._startup_urls = urls

    def set_startup_private(self, is_private: bool) -> None:
        self._startup_private = is_private

    def startup_urls(self) -> list[QUrl]:
        return self._startup_urls

    def startup_private(self) -> bool:
        return self._startup_private

    startupUrls = Property("QVariantList", startup_urls, constant=True)
    startupPrivate = Property(bool, startup_private, constant=True)
