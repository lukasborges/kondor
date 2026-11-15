from pathlib import Path

from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from kondor.browser.tabs.tabmodel import TabModel
from tests.history.historyrows import add_visit, reset_history
from tests.qmlsupport import error_text

HOST_QML = Path(__file__).resolve().parent.parent.parent / "data" / "AddressBarHost.qml"
FIRST_URL = QUrl("https://kde.org/one")
PLASMA_VISITED_AT = 1000000


def seed_history() -> None:
    reset_history()
    add_visit("https://kde.org/plasma", "Plasma", PLASMA_VISITED_AT)


class AddressBarHarness:
    def __init__(self, engine: QQmlEngine, qtbot: QtBot) -> None:
        self._qtbot = qtbot
        self.tabs = TabModel()
        self.tabs.addTab(False, FIRST_URL)
        self._component = QQmlComponent(engine, QUrl.fromLocalFile(str(HOST_QML)))
        created = self._component.createWithInitialProperties({"tabModel": self.tabs})
        assert created is not None, error_text(self._component)
        self.window: QQuickWindow = created
        qtbot.waitExposed(self.window)

    def close(self) -> None:
        self.window.close()
        self.window.deleteLater()
        self.tabs.deleteLater()

    def call(self, function: str, *arguments: object) -> object:
        holders = [Q_ARG("QVariant", argument) for argument in arguments]
        connection = Qt.ConnectionType.DirectConnection
        result = Q_RETURN_ARG("QVariant")
        return QMetaObject.invokeMethod(self.window, function, connection, result, *holders)

    def bar_property(self, name: str) -> object:
        return self.call("barProperty", name)

    def suggestions_property(self, name: str) -> object:
        return self.call("suggestionsProperty", name)

    def text(self) -> str:
        return str(self.bar_property("text"))

    def row_count(self) -> int:
        return int(self.call("suggestionRowCount"))

    def text_of_row(self, index: int) -> str:
        return str(self.call("suggestionRowText", index))

    def is_open(self) -> bool:
        return bool(self.suggestions_property("opened"))

    def type(self, typed: str) -> None:
        self._qtbot.waitUntil(lambda: bool(self.call("focusBar")))
        for letter in typed:
            QTest.keyClick(self.window, letter)

    def press(self, key: Qt.Key) -> None:
        QTest.keyClick(self.window, key)
