from typing import Any

from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QPoint, QPointF, Qt
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from kondor.core.settings.settings import Settings
from tests.browser.tabstrip.tabstripharness import create_kept

SIDE_BAR_QML = "import QtQuick\nimport Kondor\nTabSideBar {}\n"
STUB_QML = """import QtQml
QtObject {
    property var model
    function closeTabFor(tab) { model.closeTabObject(tab) }
    function closeTabAt(index) { model.closeTab(index) }
    function openGroupEditor(group, item) {}
}
"""
PROBE_QML = """import QtQuick
QtObject {
    property var sideBar
    function list() { return sideBar.children[0].children[2] }
    function row(index) { return list().itemAtIndex(index) }
    function rowCount() { return list().count }
    function point(index) {
        const item = row(index)
        return item.mapToItem(null, item.width / 2, item.height / 2)
    }
    function pointX(index) { return point(index).x }
    function pointY(index) { return point(index).y }
    function rowY(index) { return row(index).mapToItem(null, 0, 0).y }
    function headerY(index) { return row(index).children[0].mapToItem(null, 0, 0).y }
    function bars() { return countBars(list().contentItem) }
    function countBars(item) {
        let count = item.isVertical !== undefined && item.visible && item.group ? 1 : 0
        for (const child of item.children)
            count += countBars(child)
        return count
    }
}
"""
SIDE_BAR_WIDTH = 224
SIDE_BAR_HEIGHT = 600
SETTLE_MS = 50


class SideBarHarness:
    def __init__(self, engine: QQmlEngine, collapsed: bool) -> None:
        Settings.instance().setProperty("sideBarCollapsed", collapsed)
        self.tabs = TabModel()
        self.window = QQuickWindow()
        self.window.resize(SIDE_BAR_WIDTH, SIDE_BAR_HEIGHT)
        stub = create_kept(engine, STUB_QML, {"model": self.tabs})
        properties = {"tabModel": self.tabs, "targetWindow": stub}
        bar = create_kept(engine, SIDE_BAR_QML, properties)
        assert isinstance(bar, QQuickItem)
        bar.setParentItem(self.window.contentItem())
        bar.setPosition(QPointF(0, 0))
        bar.setSize(self.window.size().toSizeF())
        self.probe = create_kept(engine, PROBE_QML, {"sideBar": bar})
        self.window.show()
        QTest.qWait(SETTLE_MS)

    def close(self) -> None:
        Settings.instance().setProperty("sideBarCollapsed", False)
        self.window.close()
        self.tabs.deleteLater()

    def call(self, function: str, *arguments: object) -> Any:
        holders = [Q_ARG("QVariant", argument) for argument in arguments]
        connection = Qt.ConnectionType.DirectConnection
        result = Q_RETURN_ARG("QVariant")
        return QMetaObject.invokeMethod(self.probe, function, connection, result, *holders)

    def add_tabs(self, count: int) -> None:
        for _ in range(count):
            self.tabs.addTab()
        QTest.qWait(SETTLE_MS)

    def order(self) -> list[Tab]:
        return [self.tabs.tabAt(index) for index in range(self.tabs.count)]

    def centre_of_row(self, row: int) -> QPoint:
        return QPoint(int(self.call("pointX", row)), int(self.call("pointY", row)))

    def drag_row(self, row: int, dy: int) -> None:
        press = self.centre_of_row(row)
        self.press(press)
        self.slide(press, dy)
        self.release(press + QPoint(0, dy))

    def press(self, point: QPoint) -> None:
        QTest.mousePress(
            self.window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
        )

    def release(self, point: QPoint) -> None:
        QTest.mouseRelease(
            self.window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
        )
        QTest.qWait(SETTLE_MS)

    def row_y(self, row: int) -> float:
        return float(self.call("rowY", row))

    def header_y(self, row: int) -> float:
        return float(self.call("headerY", row))

    def slide(self, press: QPoint, dy: int) -> None:
        step = 5 if dy > 0 else -5
        for distance in range(step, dy, step):
            QTest.mouseMove(self.window, press + QPoint(0, distance))
        QTest.mouseMove(self.window, press + QPoint(0, dy))
        QTest.qWait(SETTLE_MS)

    def rows(self) -> int:
        return int(self.call("rowCount"))

    def visible_bars(self) -> int:
        return int(self.call("bars"))
