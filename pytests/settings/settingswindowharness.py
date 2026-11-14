from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QCoreApplication, QEvent, QMetaObject, QObject, Qt
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from kondor.browser.tabs.tabmodel import TabModel
from kondor.core.settings.settings import Settings
from pytests.qmlsupport import error_text, load_component

WINDOW_WIDTH = 860
WINDOW_HEIGHT = 600
SETTINGS_WINDOW_QML = "import QtQuick\nimport Kondor\nSettingsWindow {}\n"
KEPT_COMPONENTS: list[QQmlComponent] = []
CHANGED_OPTION_PER_PAGE: list[tuple[str, object]] = [
    ("homePage", "https://kde.org"),
    ("searchEngine", "google"),
    ("askWhereToSave", True),
    ("blockThirdPartyCookies", True),
    ("offerToSavePasswords", False),
    ("extensionsAutoUpdate", False),
    ("spellCheckEnabled", False),
]
TEST_DEFAULTS: dict[str, object] = {
    "homePage": "",
    "searchEngine": "duckduckgo",
    "customSearchUrl": "",
    "askWhereToSave": False,
    "startupBehavior": "homepage",
    "showTopSites": True,
    "clearDataOnExit": False,
    "blockThirdPartyCookies": False,
}


def reset_settings_to_test_defaults() -> None:
    settings = Settings.instance()
    for name, value in TEST_DEFAULTS.items():
        settings.setProperty(name, value)


def pending_of(parent: QObject) -> QObject | None:
    for child in parent.children():
        if child.property("searchEngine") is not None:
            return child
        found = pending_of(child)
        if found is not None:
            return found
    return None


def create_settings_window(engine: QQmlEngine, tabs: TabModel) -> QQuickWindow:
    component = load_component(engine, SETTINGS_WINDOW_QML)
    created = component.createWithInitialProperties({"tabModel": tabs})
    assert isinstance(created, QQuickWindow), error_text(component)
    QQmlEngine.setObjectOwnership(created, QQmlEngine.ObjectOwnership.CppOwnership)
    KEPT_COMPONENTS.append(component)
    created.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
    return created


class SettingsWindowHarness:
    def __init__(self, engine: QQmlEngine) -> None:
        self.tabs = TabModel()
        self.window = create_settings_window(engine, self.tabs)

    def pending(self) -> QObject:
        found = pending_of(self.window)
        assert found is not None
        return found

    def is_modified(self) -> bool:
        return bool(self.window.property("modified"))

    def invoke(self, method: str) -> None:
        QMetaObject.invokeMethod(self.window, method)

    def show_window(self) -> None:
        self.invoke("showWindow")

    def show_exposed(self) -> bool:
        self.show_window()
        return bool(QTest.qWaitForWindowExposed(self.window))

    def child(self, object_name: str) -> QObject:
        found = self.window.findChild(QObject, object_name)
        assert found is not None, object_name
        return found

    def sidebar_entry(self, index: int) -> QObject | None:
        connection = Qt.ConnectionType.DirectConnection
        result = Q_RETURN_ARG(QQuickItem)
        entry = QMetaObject.invokeMethod(
            self.child("pageList"), "itemAtIndex", connection, result, Q_ARG("int", index)
        )
        return entry or None

    def close(self) -> None:
        self.window.close()
        self.window.deleteLater()
        self.tabs.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
