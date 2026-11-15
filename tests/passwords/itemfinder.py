from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QObject, Qt
from PySide6.QtQml import QJSValue, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow

from tests.qmlsupport import load_component

ITEM_FINDER_QML = """import QtQuick
QtObject {
    function descendants(root) {
        return root.children.reduce((all, child) => all.concat(descendants(child)), [root])
    }
    function named(root, name) {
        return descendants(root).filter(item => item.objectName === name)
    }
    function withText(root, text) {
        return descendants(root).find(item => item.visible && item.text === text) || null
    }
    function popupRows(window) {
        return named(window.popup.contentItem, "savedAccountRow")
    }
    function popupItems(window, name) {
        return named(window.popup.contentItem, name)
    }
    function popupText(window, text) {
        return withText(window.popup.contentItem, text)
    }
    function isPopupOpened(window) {
        return window.popup.opened
    }
    function openPopup(window) {
        window.popup.open()
        return true
    }
}
"""


def items_of(array: object) -> list[QQuickItem]:
    assert isinstance(array, QJSValue)
    length = array.property("length").toInt()
    return [array.property(index).toQObject() for index in range(length)]


def item_of(value: object) -> QQuickItem | None:
    found = value.toQObject() if isinstance(value, QJSValue) else value
    return found if isinstance(found, QQuickItem) else None


class ItemFinder:
    def __init__(self, engine: QQmlEngine) -> None:
        self._component = load_component(engine, ITEM_FINDER_QML)
        self._finder = self._component.create()

    def named(self, root: QObject, name: str) -> list[QQuickItem]:
        return items_of(self._call("named", root, name))

    def with_text(self, root: QObject, text: str) -> QQuickItem | None:
        return item_of(self._call("withText", root, text))

    def popup_rows(self, window: QQuickWindow) -> list[QQuickItem]:
        return items_of(self._call("popupRows", window))

    def popup_items(self, window: QQuickWindow, name: str) -> list[QQuickItem]:
        return items_of(self._call("popupItems", window, name))

    def popup_text(self, window: QQuickWindow, text: str) -> QQuickItem | None:
        return item_of(self._call("popupText", window, text))

    def is_popup_opened(self, window: QQuickWindow) -> bool:
        return bool(self._call("isPopupOpened", window))

    def open_popup(self, window: QQuickWindow) -> None:
        self._call("openPopup", window)

    def _call(self, function: str, *arguments: object) -> object:
        holders = [Q_ARG("QVariant", argument) for argument in arguments]
        connection = Qt.ConnectionType.DirectConnection
        result = Q_RETURN_ARG("QVariant")
        return QMetaObject.invokeMethod(self._finder, function, connection, result, *holders)
