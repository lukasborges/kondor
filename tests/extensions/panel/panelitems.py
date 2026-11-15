from PySide6.QtCore import (
    Q_ARG,
    Q_RETURN_ARG,
    QMetaObject,
    QObject,
    QPointF,
    Qt,
)
from PySide6.QtGui import QAccessible
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests.qmlsupport import load_component

ROW_PROBE_QML = """import QtQuick
QtObject {
    function partsEnabled(row) {
        return Array.from(row.contentItem.children, part => part.enabled)
    }
}
"""


class RowProbe:
    def __init__(self, engine: QQmlEngine) -> None:
        self._component = load_component(engine, ROW_PROBE_QML)
        self._probe = self._component.create()

    def parts_enabled(self, row: QQuickItem) -> list[bool]:
        result = Q_RETURN_ARG("QVariant")
        connection = Qt.ConnectionType.DirectConnection
        flags = QMetaObject.invokeMethod(
            self._probe, "partsEnabled", connection, result, Q_ARG("QVariant", row)
        )
        return list(flags.toVariant())


def find_by_name(root: QObject, name: str) -> QQuickItem:
    found = root.findChild(QQuickItem, name)
    assert found is not None, name
    return found


def accessible_name_of(item: QQuickItem) -> str:
    accessible = QAccessible.queryAccessibleInterface(item)
    return str(accessible.text(QAccessible.Text.Name)) if accessible else ""


def accessible_description_of(item: QQuickItem) -> str:
    accessible = QAccessible.queryAccessibleInterface(item)
    return str(accessible.text(QAccessible.Text.Description)) if accessible else ""


def keep_alive(*objects: QObject) -> None:
    for item in objects:
        QQmlEngine.setObjectOwnership(item, QQmlEngine.ObjectOwnership.CppOwnership)


def click_center_of(item: QQuickItem) -> None:
    window = item.window()
    keep_alive(item, window)
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
    button, modifiers = Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier
    QTest.mouseClick(window, button, modifiers, center)
