import json
from collections.abc import Iterator
from contextlib import contextmanager

from PySide6.QtCore import Q_ARG, QMetaObject, QPointF, Qt
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from tests.qmlsupport import error_text, load_component

THIS_SITE = "https://example.org"
OTHER_SITE = "https://id.example.net"


def login(origin: str, host: str, username: str) -> dict[str, object]:
    return {
        "origin": origin,
        "host": host,
        "username": username,
        "isThisSite": origin == THIS_SITE,
    }


LOGINS = [
    login(THIS_SITE, "example.org", "ana"),
    login(THIS_SITE, "example.org", "bruno"),
    login(OTHER_SITE, "id.example.net", "carol"),
]

SAVED_PASSWORDS_POPUP_QML = """import QtQuick
import QtQuick.Controls
import Kondor
ApplicationWindow {
    id: window
    visible: true
    width: 500; height: 400
    property string filledLogin: ""
    property string askedUsername: ""
    property bool isPageFocused: false
    property alias popup: popup
    property alias dialog: dialog
    property bool isDialogOpened: dialog.opened
    function askToFill(login) { dialog.ask(login) }
    function acceptDialog() { dialog.accept() }
    function rejectDialog() { dialog.reject() }
    QtObject {
        id: stubTab
        function focusPage() { window.isPageFocused = true }
        property QtObject passwords: QtObject {
            signal availabilityChanged()
            signal usernamesChanged()
            signal walletStateChanged()
            property bool isAvailable: true
            property bool isWalletUnavailable: false
            property string host: "example.org"
            property var logins: __LOGINS__
            function matches(text) {
                const needle = text.trim().toLowerCase()
                return logins.filter(entry => needle === ""
                    ? entry.isThisSite
                    : (entry.host + " " + entry.username).includes(needle))
            }
            function fill(origin, username) { window.filledLogin = origin + "|" + username }
            function copyUsername(username) {}
            function copyPassword(origin, username) {}
        }
    }
    SavedPasswordsPopup {
        id: popup
        parent: Overlay.overlay
        tab: stubTab
        onOtherSiteFillRequested: function(login) { window.askedUsername = login.username }
    }
    FillFromOtherSiteDialog {
        id: dialog
        currentTab: stubTab
    }
}
"""


def popup_qml(logins: list[dict[str, object]]) -> str:
    return SAVED_PASSWORDS_POPUP_QML.replace("__LOGINS__", json.dumps(logins))


def click_center_of(window: QQuickWindow, item: QQuickItem) -> None:
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
    button, modifiers = Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier
    QTest.mouseClick(window, button, modifiers, center)


@contextmanager
def loaded_window(engine: QQmlEngine, source: str) -> Iterator[QQuickWindow]:
    component = load_component(engine, source)
    window = component.create()
    assert window is not None, error_text(component)
    QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
    yield window
    window.close()


def call(window: QQuickWindow, function: str, *arguments: object) -> None:
    holders = [Q_ARG("QVariant", argument) for argument in arguments]
    QMetaObject.invokeMethod(window, function, Qt.ConnectionType.DirectConnection, *holders)


def type_text(window: QQuickWindow, text: str) -> None:
    for character in text:
        QTest.keyClick(window, character)
