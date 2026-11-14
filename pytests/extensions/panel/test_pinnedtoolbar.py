from collections.abc import Iterator
from functools import reduce
from itertools import product

import pytest
from PySide6.QtCore import QObject, QRect, QSize, QUrl
from PySide6.QtGui import QAccessible, QImage
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot
from shiboken6 import isValid

from kondor.browser.tabs.tabmodel import TabModel
from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.package.packagefile import PackageFile
from pytests.extensions.extensionsharness import install_sample, pack_variant
from pytests.extensions.panel.panelitems import (
    accessible_name_of,
    click_center_of,
    find_by_name,
)
from pytests.qmlsupport import error_text, load_component

pytestmark = pytest.mark.no_qt_log

SAMPLE = "sample"
BUTTON_NAME = "Sample Extension"
ICON_BOX = 22
TOOL_BAR_QML = """import QtQuick
import QtQuick.Controls
import Kondor
ApplicationWindow {
    visible: true
    width: 700; height: 100
    ExtensionsToolButtons { tabs: theTabs; browserWindow: null }
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
        ExtensionManager.instance().setPinned(SAMPLE, False)


@pytest.fixture(scope="module", autouse=True)
def accessibility() -> None:
    QAccessible.setActive(True)


@pytest.fixture
def toolbar(qtbot: QtBot, work: str, kondor_engine: QQmlEngine) -> Iterator[ToolBar]:
    tool_bar = ToolBar(qtbot, kondor_engine, work)
    yield tool_bar
    tool_bar.close()


def test_pinned_extension_shows_visible_button(toolbar: ToolBar) -> None:
    toolbar.show()
    toolbar.pin()
    toolbar.qtbot.waitUntil(lambda: toolbar.button() is not None)
    button = toolbar.button()
    assert button.width() > 0
    assert button.height() > 0


def test_unpin_removes_button(toolbar: ToolBar) -> None:
    toolbar.show()
    toolbar.pin()
    toolbar.qtbot.waitUntil(lambda: toolbar.button() is not None)
    ExtensionManager.instance().setPinned(SAMPLE, False)
    toolbar.qtbot.waitUntil(lambda: toolbar.button() is None)


def test_pinned_button_opens_panel_on_extension(toolbar: ToolBar) -> None:
    toolbar.show()
    toolbar.pin()
    click_center_of(toolbar.wait_for_pinned_button())
    panel = toolbar.window.findChild(QObject, "extensionsPanel")
    assert panel is not None
    toolbar.qtbot.waitUntil(lambda: panel.property("currentId") == SAMPLE)


def test_pinned_file_icon_fits_tool_bar_icon_box(toolbar: ToolBar) -> None:
    toolbar.show()
    toolbar.pin()
    toolbar.verify_icon_fits_box(toolbar.wait_for_pinned_button())


def test_pinned_theme_icon_button_has_extensions_button_width(toolbar: ToolBar) -> None:
    toolbar.install_theme_icon_sample()
    toolbar.show()
    toolbar.pin()
    button = toolbar.wait_for_pinned_button()
    assert button.width() == toolbar.named("extensionsButton").width()


def test_pinned_theme_icon_fits_tool_bar_icon_box(toolbar: ToolBar) -> None:
    toolbar.install_theme_icon_sample()
    toolbar.show()
    toolbar.pin()
    toolbar.verify_icon_fits_box(toolbar.wait_for_pinned_button())


def test_extensions_button_icon_fits_tool_bar_icon_box(toolbar: ToolBar) -> None:
    toolbar.show()
    toolbar.verify_icon_fits_box(toolbar.named("extensionsButton"))
