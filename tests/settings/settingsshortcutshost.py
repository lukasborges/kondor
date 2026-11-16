from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QObject, QUrl
from PySide6.QtGui import QGuiApplication, QKeySequence, QWindow
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from kondor.browser.tabs.tabmodel import TabModel
from tests.qmlsupport import error_text, load_component

HOST_QML = """
import QtQuick
import QtQuick.Controls
import Kondor

ApplicationWindow {
    id: host
    property int findCount: 0
    property var settingsWindow: null
    required property TabModel tabs
    readonly property var actions: BrowserActions {
        tabs: host.tabs
        tabController: QtObject {}
        dialogs: QtObject {}
        fileDialogs: QtObject {}
        pageArea: QtObject {
            property var findBar: QtObject { function open() { host.findCount++ } }
        }
        browserWindow: host
    }
    TextField { objectName: "pageField"; anchors.fill: parent }
    Component { id: settingsComponent; SettingsWindow {} }
    function openSettings() {
        settingsWindow = settingsComponent.createObject(host, { tabModel: tabs })
        settingsWindow.showWindow()
    }
}
"""
KEPT_COMPONENTS: list[QQmlComponent] = []


def wait_for_focus_window(window: QWindow | None) -> bool:
    for _ in range(20):
        if QGuiApplication.focusWindow() is window:
            return True
        QTest.qWait(50)
    return False


def is_find_shortcut(shortcut: QObject) -> bool:
    if not shortcut.metaObject().className().startswith("WindowShortcut"):
        return False
    return QKeySequence(QKeySequence.StandardKey.Find) in shortcut.property("sequences")


class ShortcutsHost:
    def __init__(self, engine: QQmlEngine) -> None:
        self.tabs = TabModel()
        self.tabs.addTab(False, QUrl("https://kde.org"))
        component = load_component(engine, HOST_QML)
        KEPT_COMPONENTS.append(component)
        created = component.createWithInitialProperties({"tabs": self.tabs})
        assert isinstance(created, QQuickWindow), error_text(component)
        QQmlEngine.setObjectOwnership(created, QQmlEngine.ObjectOwnership.CppOwnership)
        self.window = created
        created.resize(400, 300)
        created.show()
        assert QTest.qWaitForWindowExposed(created)

    def focus(self, window: QQuickWindow) -> None:
        window.requestActivate()
        assert QTest.qWaitForWindowActive(window)
        assert wait_for_focus_window(window)
        QCoreApplication.processEvents()

    def focus_page_field(self) -> None:
        field = self.window.findChild(QObject, "pageField")
        assert field is not None
        self.focus(self.window)
        field.forceActiveFocus()
        QCoreApplication.processEvents()

    def settings(self) -> QQuickWindow:
        found = self.window.property("settingsWindow")
        assert isinstance(found, QQuickWindow)
        return found

    def open_settings(self) -> None:
        QMetaObject.invokeMethod(self.window, "openSettings")
        assert QTest.qWaitForWindowExposed(self.settings())
        QTest.qWait(200)

    def press_find(self, window: QQuickWindow) -> None:
        QTest.keySequence(window, QKeySequence(QKeySequence.StandardKey.Find))
        QTest.qWait(200)

    def focus_settings(self) -> None:
        settings = self.settings()
        self.focus(settings)
        item = settings.contentItem()
        item.forceActiveFocus()
        QCoreApplication.processEvents()

    def count_settings_find_activations(self) -> list[int]:
        activations: list[int] = []
        for shortcut in self.settings().findChildren(QObject):
            if is_find_shortcut(shortcut):
                shortcut.activated.connect(lambda: activations.append(1))
        return activations

    def find_count(self) -> int:
        return int(self.window.property("findCount"))

    def close(self) -> None:
        for window in (self.window.property("settingsWindow"), self.window):
            if window is not None:
                window.close()
                window.deleteLater()
        self.tabs.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        wait_for_focus_window(None)
