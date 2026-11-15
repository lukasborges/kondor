from typing import Any

from PySide6.QtCore import QDir, QLoggingCategory, QObject, Signal, qCInfo, qCWarning
from PySide6.QtWebEngineCore import QWebEngineExtensionInfo, QWebEngineExtensionManager
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

CATEGORY = QLoggingCategory("kondor.extensions")


def log_info(message: str) -> None:
    qCInfo(CATEGORY, message)


def manager_for(profile: QQuickWebEngineProfile | None) -> QWebEngineExtensionManager | None:
    if profile is None or profile.isOffTheRecord():
        qCWarning(CATEGORY, "Extensions are never loaded into private profiles")
        return None
    manager = getattr(profile, "extensionManager", lambda: None)()
    if manager is None:
        qCWarning(CATEGORY, "Extensions are not supported by this Qt WebEngine build")
    return manager


def requested_directories(directories: list[str]) -> dict[str, str]:
    return {QDir.cleanPath(QDir(directory).absolutePath()): directory for directory in directories}


def enable_loaded_extension(info: QWebEngineExtensionInfo, manager: Any) -> None:
    if not info.isEnabled():
        manager.setExtensionEnabled(info, True)


def log_loaded(info: QWebEngineExtensionInfo) -> None:
    popup = info.actionPopupUrl()
    shown = "none" if popup.isEmpty() else popup.toString()
    log_info(f"Extension loaded: {info.name()} ({info.id()}) popup: {shown}")


def log_failed(info: QWebEngineExtensionInfo, directory: str) -> None:
    log_info(f"Extension failed: {directory}: {info.error()}")


class ExtensionLoader(QObject):
    loadFinished = Signal(str, bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    @staticmethod
    def is_supported() -> bool:
        return True

    def load(self, profile: QQuickWebEngineProfile | None, directories: list[str]) -> None:
        if directories:
            self.load_into(profile, directories)

    def handle_load_finished(
        self, info: QWebEngineExtensionInfo, requested: dict[str, str], manager: Any
    ) -> None:
        directory = requested.get(QDir.cleanPath(info.path()), info.path())
        if info.isLoaded():
            enable_loaded_extension(info, manager)
            log_loaded(info)
        else:
            log_failed(info, directory)
        self.loadFinished.emit(directory, info.isLoaded())

    def load_into(self, profile: QQuickWebEngineProfile | None, directories: list[str]) -> None:
        manager = manager_for(profile)
        if manager is None:
            return
        requested = requested_directories(directories)
        manager.loadFinished.connect(
            lambda info: self.handle_load_finished(info, requested, manager)
        )
        for directory in directories:
            manager.loadExtension(QDir(directory).absolutePath())
