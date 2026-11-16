from collections.abc import Iterator
from typing import Any

import pytest
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QObject, QRectF, Qt
from PySide6.QtQml import QQmlEngine

from kondor.browser.tabs.tab import Tab
from kondor.core.settings.settings import Settings
from tests.browser.pagecontextmenucases import (
    CASES,
    MISSPELLED_FIELD,
    SEARCH_PLACEHOLDER,
    SEPARATOR,
    complete_request,
    search_item,
)
from tests.qmlsupport import error_text, load_component

pytestmark = pytest.mark.no_qt_log

HOST_QML = """import QtQuick
import QtQuick.Controls
import QtWebEngine
import Kondor

Item {
    id: root
    property var menu: pageMenu
    property var tab: null
    WebEngineView { id: view }
    QtObject {
        id: browserActions
        property Action savePageAction: Action { enabled: true }
        property Action printAction: Action { enabled: true }
    }
    PageContextMenu { id: pageMenu; webView: view; tab: root.tab; browserActions: browserActions }

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
    tab = Tab(None)
    created.setProperty("tab", tab)
    yield created
    del tab
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


def test_password_field_starts_with_generate_password(host: QObject) -> None:
    host.property("tab").passwords.suggestion.show_field("password", False, QRectF())
    items = items_for(host, MISSPELLED_FIELD)
    assert items[:2] == ["Generate Password", SEPARATOR]


def test_other_fields_have_no_generate_password(host: QObject) -> None:
    assert "Generate Password" not in items_for(host, MISSPELLED_FIELD)
