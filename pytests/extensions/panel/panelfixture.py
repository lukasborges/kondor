from collections.abc import Callable
from dataclasses import dataclass, field

from PySide6.QtCore import (
    Q_ARG,
    Q_RETURN_ARG,
    QCoreApplication,
    QEvent,
    QMetaObject,
    QObject,
    Qt,
    QUrl,
)
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from pytestqt.qtbot import QtBot
from shiboken6 import isValid

from kondor.browser.tabs.tab import Tab
from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.package.packagefile import PackageFile
from pytests.extensions.extensionsharness import install_sample, pack_variant
from pytests.extensions.panel.panelitems import RowProbe, click_center_of, find_by_name
from pytests.passwords.itemfinder import ItemFinder
from pytests.qmlsupport import error_text, load_component

PAGE_URL = "https://www.example.com/page"
PANEL_WINDOW_QML = """import QtQuick
import QtQuick.Controls
import Kondor
ApplicationWindow {
    visible: true
    width: 700; height: 600
    ExtensionsPanel {
        id: panel; objectName: "panel"; parent: Overlay.overlay; x: 100; y: 50; tab: theTab
    }
    SiteReloadBar { id: bar; objectName: "bar"; tab: theTab; width: parent.width }
}
"""
KEYED_SETTING = {
    "key": "keyGo",
    "type": "keys",
    "label": "Go",
    "default": "S",
}
KEYED_ITEMS = [
    {"id": "go", "title": "Go Now", "keysSetting": "keyGo"},
    {"id": "mark", "title": "Mark", "checkable": True, "keysSetting": "keyGo"},
]


def install_keyed(work: str) -> bool:
    def edit(manifest: dict) -> None:
        manifest.update(id="keyed", name="Keyed", settings=[KEYED_SETTING])
        manifest["action"] = {"items": KEYED_ITEMS}

    zip_path = pack_variant(work, "keyed", edit)
    file = PackageFile(zip_path, "file")
    return ExtensionManager.instance().install_package(file, "keyed").is_installed


@dataclass
class PanelFixture:
    qtbot: QtBot
    engine: QQmlEngine
    work: str
    tab: Tab | None = None
    window: QQuickWindow | None = None
    panel: QObject | None = None
    components: list[QQmlComponent] = field(default_factory=list)
    rows: list[QQuickItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.finder = ItemFinder(self.engine)
        self.probe = RowProbe(self.engine)

    def make_tab(self, tab: Tab) -> None:
        self.tab = tab
        tab.setUrl(QUrl(PAGE_URL))

    def open_panel(self, extension_id: str = "") -> None:
        if ExtensionManager.instance().count == 0:
            assert install_sample(self.work)
        if self.tab is None:
            self.make_tab(Tab(None))
            self.tab.extensionItems.setChecked("sample", "toggle", True)
        self.engine.rootContext().setContextProperty("theTab", self.tab)
        self.create_window()
        self.show_panel(extension_id)

    def create_window(self) -> None:
        component = load_component(self.engine, PANEL_WINDOW_QML)
        self.components.append(component)
        window = component.create()
        assert window is not None, error_text(component)
        QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
        self.window = window
        self.panel = window.findChild(QObject, "panel")

    def show_panel(self, extension_id: str) -> None:
        assert self.panel is not None
        if extension_id:
            QMetaObject.invokeMethod(self.panel, "openAt", Q_ARG("QVariant", extension_id))
        else:
            QMetaObject.invokeMethod(self.panel, "open")
        self.qtbot.waitUntil(lambda: bool(self.panel.property("opened")))

    def item(self, name: str) -> QQuickItem:
        assert self.window is not None
        return find_by_name(self.window, name)

    def row_at(self, index: int) -> QQuickItem | None:
        connection = Qt.ConnectionType.DirectConnection
        row = QMetaObject.invokeMethod(
            self.item("panelExtensionList"),
            "itemAtIndex",
            connection,
            Q_RETURN_ARG("QQuickItem*"),
            Q_ARG(int, index),
        )
        if not isinstance(row, QQuickItem):
            return None
        QQmlEngine.setObjectOwnership(row, QQmlEngine.ObjectOwnership.CppOwnership)
        self.rows.append(row)
        return row

    def item_with_text(self, root: QQuickItem, text: str) -> QQuickItem | None:
        return self.finder.with_text(root, text)

    def actions_root(self) -> QQuickItem:
        return self.item("backButton").parentItem().parentItem()

    def current_id(self) -> str:
        assert self.panel is not None
        return str(self.panel.property("currentId"))

    def toggle_run_on_site(self) -> None:
        click_center_of(self.item("siteSwitch"))

    def wait_for(self, condition: Callable[[], object]) -> None:
        self.qtbot.waitUntil(lambda: bool(condition()))

    def reset(self) -> None:
        if self.window is not None and isValid(self.window):
            self.window.close()
            self.window.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.window = None
        self.panel = None
        self.tab = None
        self.engine.rootContext().setContextProperty("theTab", None)
