from functools import reduce
from itertools import product

from PySide6.QtCore import QCoreApplication, QEvent, QRect, QSize, QUrl
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot
from shiboken6 import isValid

from kondor.app.startup.appidentity import use_bundled_icons
from kondor.browser.tabs.tabmodel import TabModel
from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.package.packagefile import PackageFile
from tests.extensions.extensionsharness import install_sample, pack_variant
from tests.extensions.panel.panelitems import (
    accessible_name_of,
    find_by_name,
)
from tests.qmlsupport import error_text, load_component

SAMPLE = "sample"
BUTTON_NAME = "Sample Extension"
ICON_BOX = 22
STRONG_RED = 200
TOOL_BAR_QML = """import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import Kondor
ApplicationWindow {
    visible: true
    width: 700; height: 100
    Item {
        Kirigami.Theme.inherit: false
        Kirigami.Theme.colorSet: Kirigami.Theme.Custom
        Kirigami.Theme.textColor: "#ff0000"
        ExtensionsToolButtons { tabs: theTabs; browserWindow: null }
    }
}
"""


def paint_bounds_of(image: QImage) -> QSize:
    background = image.pixel(0, 0)
    points = product(range(image.width()), range(image.height()))
    painted = [QRect(x, y, 1, 1) for x, y in points if image.pixel(x, y) != background]
    return reduce(QRect.united, painted, QRect()).size()


def icon_size_of(button: QQuickItem) -> QSize:
    area = button.mapRectToScene(button.boundingRect())
    return paint_bounds_of(button.window().grabWindow().copy(area.toAlignedRect()))


def find_named_button(root: QQuickItem, name: str) -> QQuickItem | None:
    pending = [root]
    while pending:
        item = pending.pop()
        if item.isVisible() and accessible_name_of(item) == name:
            return item
        for child in item.childItems():
            QQmlEngine.setObjectOwnership(child, QQmlEngine.ObjectOwnership.CppOwnership)
            pending.append(child)
    return None


class ToolBar:
    def __init__(self, qtbot: QtBot, engine: QQmlEngine, work: str) -> None:
        self.qtbot, self.engine, self.work = qtbot, engine, work
        self.tabs = TabModel()
        self.window: QQuickWindow | None = None
        self.component = None
        self.found: list[QQuickItem | None] = []
        self.content: QQuickItem | None = None

    def install_theme_icon_sample(self) -> None:
        zip_path = pack_variant(
            self.work, "theme", lambda manifest: manifest.update(icon="plugins")
        )
        installed = ExtensionManager.instance().install_package(
            PackageFile(zip_path, "file"), SAMPLE
        )
        assert installed.is_installed, installed.error

    def show(self) -> None:
        if ExtensionManager.instance().count == 0:
            assert install_sample(self.work)
        use_bundled_icons()
        self.tabs.addTab(False, QUrl("https://www.example.com/page"))
        self.engine.rootContext().setContextProperty("theTabs", self.tabs)
        self.component = load_component(self.engine, TOOL_BAR_QML)
        window = self.component.create()
        assert window is not None, error_text(self.component)
        QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
        self.window = window
        self.content = window.contentItem()
        assert QTest.qWaitForWindowExposed(window)

    def button(self) -> QQuickItem | None:
        found = find_named_button(self.content, BUTTON_NAME)
        self.found.append(found)
        return found

    def named(self, name: str) -> QQuickItem:
        return find_by_name(self.window, name)

    def is_pinned_button_laid_out(self) -> bool:
        button = self.button()
        return button is not None and self.named("extensionsButton").x() >= button.width()

    def pin(self) -> None:
        ExtensionManager.instance().setPinned(SAMPLE, True)

    def wait_for_pinned_button(self) -> QQuickItem:
        self.qtbot.waitUntil(self.is_pinned_button_laid_out)
        return self.button()

    def verify_icon_fits_box(self, button: QQuickItem) -> None:
        self.qtbot.waitUntil(lambda: not icon_size_of(button).isEmpty())
        size = icon_size_of(button)
        assert size.boundedTo(QSize(ICON_BOX, ICON_BOX)) == size

    def close(self) -> None:
        if self.window is not None and isValid(self.window):
            self.window.close()
            self.window.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        ExtensionManager.instance().setPinned(SAMPLE, False)


def has_red_pixel(button: QQuickItem) -> bool:
    area = button.mapRectToScene(button.boundingRect()).toAlignedRect()
    image = button.window().grabWindow().copy(area)
    points = product(range(image.width()), range(image.height()))
    colors = (image.pixelColor(x, y) for x, y in points)
    return any(color.red() >= STRONG_RED > color.green() for color in colors)
