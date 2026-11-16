from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from pytestqt.qtbot import QtBot

from tests.qmlsupport import error_text, load_component

pytestmark = pytest.mark.no_qt_log

WINDOW_QML = """import QtQuick
import QtQuick.Controls
import Kondor
import "file:%s/qml/bookmarks/dialogs"
import "file:%s/qml/history"
import "file:%s/qml/extensions"
ApplicationWindow {
    visible: true
    width: 800; height: 400
    Component.onCompleted: {
        const button = dialog.standardButton(Dialog.Cancel) ?? dialog.standardButton(Dialog.Close)
        button.objectName = dialog.standardButtons & Dialog.Close ? "closeButton" : "cancelButton"
    }
    property var dialog: %s
}
"""


HEADER_INSET = 8
TOLERANCE = 2


def right_edge(item: QQuickItem) -> float:
    return item.mapToScene(QPointF(item.width(), 0)).x()


def left_edge(item: QQuickItem) -> float:
    return item.mapToScene(QPointF(0, 0)).x()


def open_dialog(
    qtbot: QtBot, engine: QQmlEngine, source: str
) -> tuple[QObject, QObject, QQmlComponent]:
    root = Path(__file__).resolve().parents[2]
    component = load_component(engine, WINDOW_QML % (root, root, root, source))
    window = component.create()
    assert window is not None, error_text(component)
    QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
    qtbot.waitExposed(window)
    dialog = window.findChild(QObject, "dialog")
    dialog.open()
    qtbot.waitUntil(lambda: bool(dialog.property("opened")))
    return window, dialog, component


@pytest.mark.parametrize(
    "source",
    [
        'NewBookmarkFolderDialog { objectName: "dialog"; selection: null }',
        'RenameBookmarkDialog { objectName: "dialog" }',
    ],
)
def test_cancel_button_lines_up_with_the_field(
    qtbot: QtBot, kondor_engine: QQmlEngine, source: str
) -> None:
    window, dialog, component = open_dialog(qtbot, kondor_engine, source)
    field = window.findChild(QObject, "nameField")
    cancel = window.findChild(QObject, "cancelButton")
    assert abs(right_edge(cancel) - right_edge(field)) <= 1


def test_catalog_close_button_lines_up_with_the_search_field(
    qtbot: QtBot, kondor_engine: QQmlEngine
) -> None:
    window, dialog, component = open_dialog(
        qtbot, kondor_engine, 'ExtensionCatalogDialog { objectName: "dialog" }'
    )
    field = window.findChild(QObject, "searchField")
    close = window.findChild(QObject, "closeButton")
    assert abs(right_edge(close) - right_edge(field)) <= 1


def test_clear_history_label_starts_at_the_title_edge(
    qtbot: QtBot, kondor_engine: QQmlEngine
) -> None:
    window, dialog, component = open_dialog(
        qtbot, kondor_engine, 'ClearHistoryDialog { objectName: "dialog" }'
    )
    label = window.findChild(QObject, "rangeLabel")
    header = dialog.property("header")
    assert abs(left_edge(label) - left_edge(header) - HEADER_INSET) <= TOLERANCE
