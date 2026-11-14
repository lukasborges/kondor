from collections.abc import Iterator
from typing import Any

import pytest
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QObject, Qt
from PySide6.QtQml import QQmlEngine

from kondor.core.settings.settings import Settings
from pytests.browser.pagecontextmenucases import (
    CASES,
    SEARCH_PLACEHOLDER,
    SEPARATOR,
    complete_request,
    search_item,
)
from pytests.qmlsupport import error_text, load_component

pytestmark = pytest.mark.no_qt_log

HOST_QML = """import QtQuick
import QtQuick.Controls
import QtWebEngine
import Kondor

Item {
    property var menu: pageMenu
    WebEngineView { id: view }
    PageContextMenu { id: pageMenu; webView: view }

    function itemsFor(request) {
        pageMenu.request = request
        pageMenu.rebuild()
        const items = []
        for (let index = 0; index < pageMenu.count; ++index) {
            const item = pageMenu.itemAt(index)
            const isSeparator = item.toString().indexOf("MenuSeparator") >= 0
            items.push(isSeparator ? "-" : item.text)
        }
        return items
    }
}
"""


@pytest.fixture
def host(kondor_engine: QQmlEngine) -> Iterator[QObject]:
    Settings.instance().setProperty("spellCheckEnabled", False)
    component = load_component(kondor_engine, HOST_QML)
    created = component.create()
    assert created is not None, error_text(component)
    yield created
    created.deleteLater()


def items_for(host: QObject, request: dict[str, Any]) -> list[str]:
    connection = Qt.ConnectionType.DirectConnection
    result = Q_RETURN_ARG("QVariant")
    argument = Q_ARG("QVariant", complete_request(request))
    items = QMetaObject.invokeMethod(host, "itemsFor", connection, result, argument)
    return [str(item) for item in items.toVariant()]


@pytest.mark.parametrize("case", CASES, ids=[case.name for case in CASES])
def test_shows_the_blocks_of_the_request(host: QObject, case: Any) -> None:
    expected = [search_item() if item == SEARCH_PLACEHOLDER else item for item in case.items]
    assert items_for(host, case.request) == expected


def test_never_doubles_or_ends_with_a_separator(host: QObject) -> None:
    for request in [{}, *(case.request for case in CASES)]:
        items = items_for(host, request)
        assert items[0] != SEPARATOR
        assert items[-1] != SEPARATOR
        assert all(not (a == b == SEPARATOR) for a, b in zip(items, items[1:], strict=False))
