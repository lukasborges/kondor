from dataclasses import dataclass, field
from typing import Any

from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from kondor.browser.tabs.tabmodelrows import TAB_ROLE
from tests.browser.tabstrip.tabstripprobe import PROBE_QML, STRIP_QML, STUB_WINDOW_QML
from tests.qmlsupport import error_text, load_component

STRIP_ROW_Y = 18
STRIP_WIDTH = 1100
STRIP_HEIGHT = 36
WINDOW_HEIGHT = 60
SETTLE_MS = 50


@dataclass
class DragSession:
    dragged: Tab
    press: QPoint
    start_left: float
    before: list[Tab] = field(default_factory=list)


KEPT_COMPONENTS: list[QQmlComponent] = []


def create_kept(engine: QQmlEngine, source: str, properties: dict[str, object]) -> QObject:
    component = load_component(engine, source)
    created = component.createWithInitialProperties(properties)
    assert created is not None, error_text(component)
    KEPT_COMPONENTS.append(component)
    return created


class TabStripHarness:
    def __init__(self, engine: QQmlEngine, qtbot: QtBot) -> None:
        self._engine = engine
        self._qtbot = qtbot
        self.tabs = TabModel()
        self.window = QQuickWindow()
        self.window.resize(STRIP_WIDTH, WINDOW_HEIGHT)
        self._stub = create_kept(engine, STUB_WINDOW_QML, {"model": self.tabs})
        self.strip = self._create_strip()
        self.probe = create_kept(engine, PROBE_QML, {"strip": self.strip, "model": self.tabs})
        self._attach_strip()

    def _create_strip(self) -> QQuickItem:
        properties = {"tabModel": self.tabs, "targetWindow": self._stub}
        strip = create_kept(self._engine, STRIP_QML, properties)
        assert isinstance(strip, QQuickItem)
        return strip

    def _attach_strip(self) -> None:
        self.strip.setParentItem(self.window.contentItem())
        self.strip.setPosition(QPointF(0, 0))
        self.resize(STRIP_WIDTH)
        self.window.show()
        QTest.mouseMove(self.window, QPoint(500, 58))

    def close(self) -> None:
        self.window.close()
        self.window.deleteLater()
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

    def resize(self, width: int) -> None:
        self.call("resize", width)
        QTest.qWait(SETTLE_MS)

    def order(self) -> list[Tab]:
        return [self.tab_at(index) for index in range(self.tabs.count)]

    def tab_at(self, index: int) -> Tab:
        tab = self.tabs.data(self.tabs.index(index, 0), TAB_ROLE)
        assert isinstance(tab, Tab)
        return tab

    def strip_property(self, name: str) -> Any:
        return self.call("stripProp", name)

    def view_property(self, name: str) -> Any:
        return self.call("viewProp", name)

    def button_property(self, button: str, name: str) -> Any:
        return self.call("buttonProp", button, name)

    def tab_width(self) -> float:
        return float(self.strip_property("tabWidth"))

    def scrolled(self) -> float:
        return float(self.strip_property("scrolled"))

    def left_of(self, index: int) -> float:
        return float(self.call("leftOf", index))

    def left_of_tab(self, tab: Tab) -> float:
        return float(self.call("leftOfTab", tab))

    def label_left(self, group: object) -> float:
        return float(self.call("leftOfLabel", group))

    def label_width(self, group: object) -> float:
        return float(self.call("widthOfLabel", group))

    def visible_bars(self) -> int:
        return int(self.call("visibleBars"))

    def width_of(self, index: int) -> float:
        return float(self.call("widthOf", index))

    def scroll_to(self, position: float) -> None:
        self.call("scrollTo", position)

    def close_with_mouse(self, tab: Tab) -> None:
        self.call("closeWithMouse", tab)

    def click_button(self, button: str) -> None:
        x, y = self.call("buttonCenterX", button), self.call("buttonCenterY", button)
        self.click(QPoint(int(x), int(y)))

    def press_on_tab(self, index: int, offset: int) -> DragSession:
        left = self.left_of(index)
        press = QPoint(int(left) + offset, STRIP_ROW_Y)
        session = DragSession(self.tab_at(index), press, left, self.order())
        self.press(press)
        return session

    def press(self, point: QPoint) -> None:
        button, modifier = Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier
        QTest.mousePress(self.window, button, modifier, point)

    def move_mouse(self, point: QPoint) -> None:
        QTest.mouseMove(self.window, point)

    def drag_by(self, session: DragSession, dx: int) -> None:
        step = -5 if dx < 0 else 5
        for distance in range(step, dx, step):
            self.move_mouse(session.press + QPoint(distance, 0))
        self.move_mouse(session.press + QPoint(dx, 0))
        QTest.qWait(60)

    def release(self, point: QPoint, button: Qt.MouseButton = Qt.MouseButton.LeftButton) -> None:
        QTest.mouseRelease(self.window, button, Qt.KeyboardModifier.NoModifier, point)

    def release_drag(self, session: DragSession, dx: int) -> None:
        self.release(session.press + QPoint(dx, 0))

    def click(self, point: QPoint, button: Qt.MouseButton = Qt.MouseButton.LeftButton) -> None:
        QTest.mouseClick(self.window, button, Qt.KeyboardModifier.NoModifier, point)

    def drag_shift_of(self, session: DragSession) -> float:
        return float(self.call("dragShiftOf", session.dragged))

    def dragged_left(self, session: DragSession) -> float:
        return self.left_of_tab(session.dragged)

    def settle(self, session: DragSession) -> None:
        self._qtbot.waitUntil(lambda: self.drag_shift_of(session) == 0.0)

    def release_and_settle(self, session: DragSession, dx: int) -> None:
        self.release_drag(session, dx)
        self.settle(session)
