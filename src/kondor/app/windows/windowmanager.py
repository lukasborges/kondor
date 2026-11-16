from typing import ClassVar

import shiboken6
from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot, qWarning
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow

from kondor.app.instance.singleinstancemessage import SingleInstanceMessage
from kondor.app.windows import windowlaunch
from kondor.app.windows.windowcontents import WindowContents, initial_properties
from kondor.browser.profile.profilemanager import ProfileManager


def urls_from_script(values: list[object] | None) -> list[QUrl]:
    return [QUrl(value) if isinstance(value, str) else value for value in values or []]


class WindowManager(QObject):
    windowCountChanged = Signal()
    _instance: ClassVar["WindowManager | None"] = None

    def __init__(self) -> None:
        super().__init__()
        self._engine: QQmlEngine | None = None
        self._component: QQmlComponent | None = None
        self._windows: list[QObject] = []
        self._active_window: QObject | None = None

    @classmethod
    def instance(cls) -> "WindowManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_engine(self, engine: QQmlEngine | None) -> None:
        if engine is not None and self._engine is None:
            self._engine = engine

    def windows(self) -> list[QObject]:
        return [window for window in self._windows if shiboken6.isValid(window)]

    def window_count(self) -> int:
        return len(self._windows)

    windowCount = Property(int, window_count, notify=windowCountChanged)

    @Slot(result=QObject)
    @Slot(bool, result=QObject)
    @Slot(bool, "QVariantList", result=QObject)
    def newWindow(
        self, private_window: bool = False, urls: list[object] | None = None
    ) -> QObject | None:
        return self.create_window(WindowContents(private_window, urls_from_script(urls)))

    @Slot(QObject)
    def closeWindow(self, window: QObject | None) -> None:
        if window is not None:
            window.deleteLater()

    def release_windows(self) -> None:
        windows, self._windows = self._windows, []
        self._active_window = None
        self._component = None
        for window in windows:
            if shiboken6.isValid(window):
                shiboken6.delete(window)

    def component(self) -> QQmlComponent | None:
        if self._component is not None:
            return self._component
        if self._engine is not None:
            return self.load_component()
        qWarning("Kondor: cannot create a window before the QML engine is set")
        return None

    def load_component(self) -> QQmlComponent | None:
        component = QQmlComponent(self._engine, "Kondor", "BrowserWindow")
        if not component.isError():
            self._component = component
            return component
        qWarning(f"Kondor: cannot load the browser window: {component.errorString()}")
        return None

    def create_window(self, contents: WindowContents) -> QObject | None:
        component = None if self.is_refused(contents) else self.component()
        if component is None:
            return None
        window = component.createWithInitialProperties(initial_properties(contents))
        if window is None:
            qWarning(f"Kondor: cannot create the browser window: {component.errorString()}")
            return None
        self.track(window)
        return window

    @staticmethod
    def is_refused(contents: WindowContents) -> bool:
        return contents.is_private and not ProfileManager.instance().is_private_browsing_available()

    def track(self, window: QObject) -> None:
        QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
        self._windows.append(window)
        self._active_window = window
        self.follow_activity(window)
        self.windowCountChanged.emit()
        window.destroyed.connect(self.forget_closed_window)

    def follow_activity(self, window: QObject) -> None:
        if isinstance(window, QQuickWindow):
            window.activeChanged.connect(self.remember_active_sender)

    def remember_active_sender(self) -> None:
        window = self.sender()
        if isinstance(window, QQuickWindow) and window.isActive():
            self._active_window = window

    def forget_closed_window(self, closed: QObject | None = None) -> None:
        self._windows = [w for w in self._windows if w is not closed and shiboken6.isValid(w)]
        if not self.is_alive(self._active_window):
            self._active_window = self._windows[-1] if self._windows else None
        self.windowCountChanged.emit()

    @staticmethod
    def is_alive(window: QObject | None) -> bool:
        return window is not None and shiboken6.isValid(window)

    def window_for_request(self, private: bool) -> QObject | None:
        active = self._active_window
        if self.is_alive(active) and self.is_private_window(active) == private:
            return active
        matching = [w for w in self._windows if self.is_private_window(w) == private]
        return matching[-1] if matching else None

    @staticmethod
    def is_private_window(window: QObject | None) -> bool:
        return window is not None and window.property("privateWindow") is True

    def handle_single_instance_message(self, message: SingleInstanceMessage) -> None:
        windowlaunch.handle_single_instance_message(self, message)

    def open_startup_windows(self) -> None:
        windowlaunch.open_startup_windows(self)

    @Slot()
    def show_extensions_settings(self) -> None:
        windowlaunch.show_extensions_settings(self)
