from collections.abc import Iterator
from typing import Any

import pytest
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QObject, QPoint, Qt
from PySide6.QtQml import QJSValue, QQmlEngine
from pytestqt.qtbot import QtBot

from kondor.extensions.extensionmanager import ExtensionManager
from pytests.extensions.extensionsharness import install_sample
from pytests.qmlsupport import error_text, load_component

PAGE_QML = """import QtQuick
import QtQuick.Controls
import Kondor
ApplicationWindow {
    visible: true
    width: 700; height: 400
    ExtensionsPage { anchors.fill: parent }
}
"""
FINDER_QML = """import QtQuick
QtObject {
    function itemWithText(root, text) {
        if (root.visible && root.text === text)
            return root
        for (const child of root.children) {
            const found = itemWithText(child, text)
            if (found)
                return found
        }
        return null
    }
    function center(item) {
        return item.mapToItem(null, item.width / 2, item.height / 2)
    }
    function rowIsEnabled(list, index) {
        const row = list.itemAtIndex(index)
        return row ? row.enabled : null
    }
}
"""
WAIT_MILLISECONDS = 10000


class Page:
    def __init__(self, engine: QQmlEngine) -> None:
        self.page_component = load_component(engine, PAGE_QML)
        self.finder_component = load_component(engine, FINDER_QML)
        self.window = self.page_component.create()
        assert self.window is not None, error_text(self.page_component)
        self.finder = self.finder_component.create()
        QQmlEngine.setObjectOwnership(self.window, QQmlEngine.ObjectOwnership.CppOwnership)

    def call(self, name: str, *arguments: Any) -> Any:
        values = [Q_ARG("QVariant", argument) for argument in arguments]
        result = QMetaObject.invokeMethod(
            self.finder, name, Qt.ConnectionType.DirectConnection, Q_RETURN_ARG("QVariant"), *values
        )
        return result.toVariant() if isinstance(result, QJSValue) else result

    def item(self, name: str) -> QObject:
        found = self.window.findChild(QObject, name)
        assert found is not None
        return found


@pytest.fixture
def page(kondor_engine: QQmlEngine, work: str) -> Iterator[Page]:
    created = Page(kondor_engine)
    yield created
    created.window.deleteLater()


def point_of(position: Any) -> QPoint:
    return QPoint(int(position.x()), int(position.y()))


def is_dialog_open(window: QObject, title: str) -> bool:
    return any(
        child.property("title") == title and child.property("opened")
        for child in window.findChildren(QObject)
    )


def test_extensions_page_lists_installed(qtbot: QtBot, page: Page, work: str) -> None:
    extension_list = page.item("extensionList")
    assert extension_list.property("count") == 0
    assert install_sample(work)
    qtbot.waitUntil(lambda: extension_list.property("count") == 1, timeout=WAIT_MILLISECONDS)
    ExtensionManager.instance().setEnabled("sample", False)
    qtbot.waitUntil(lambda: page.call("rowIsEnabled", extension_list, 0) is not None)
    assert page.call("rowIsEnabled", extension_list, 0)


def test_empty_list_button_opens_catalog(qtbot: QtBot, page: Page) -> None:
    parent = page.item("extensionList").parent()
    qtbot.waitUntil(lambda: page.call("itemWithText", parent, "Get New Extensions…") is not None)
    button = page.call("itemWithText", parent, "Get New Extensions…")
    center = page.call("center", button)
    qtbot.mouseClick(page.window, Qt.MouseButton.LeftButton, pos=point_of(center))
    qtbot.waitUntil(lambda: is_dialog_open(page.window, "Get New Extensions"))
