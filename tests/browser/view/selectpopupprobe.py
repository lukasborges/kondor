import sys

from PySide6.QtCore import QObject, QPoint, Qt, QTimer, QUrl
from PySide6.QtGui import QGuiApplication, QWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from PySide6.QtWebEngineQuick import QtWebEngineQuick
from PySide6.QtWidgets import QApplication

PAGE = (
    b"<html><body style='margin:0'><select style='width:200px;height:30px' "
    b"onchange='document.title = this.value'>"
    b"<option>a</option><option>b</option><option>c</option></select></body></html>"
)
VIEW_QML = b"""
import QtQuick
import QtQuick.Window
import QtWebEngine
Window {
    width: 400; height: 300; visible: true
    WebEngineView { id: view; objectName: "view"; anchors.fill: parent }
}
"""
SELECT_POSITION = QPoint(50, 15)
OPTION_OFFSET = QPoint(20, 30)


def popup_window() -> QWindow | None:
    for window in QGuiApplication.topLevelWindows():
        if window.flags() & Qt.WindowType.WindowType_Mask == Qt.WindowType.Popup:
            return window
    return None


def click_second_option() -> None:
    popup = popup_window()
    if popup is None:
        return finish("no popup window")
    QTest.mouseClick(
        popup, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, OPTION_OFFSET
    )
    QTimer.singleShot(1500, report_title)


def report_title() -> None:
    finish(f"title={view().property('title')}")


def view() -> QObject:
    return window.findChild(QObject, "view")


def finish(message: str) -> None:
    print(message, flush=True)
    app.exit(0)


def open_select() -> None:
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, SELECT_POSITION
    )
    QTimer.singleShot(1500, click_second_option)


if __name__ == "__main__":
    QtWebEngineQuick.initialize()
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()
    engine.loadData(VIEW_QML)
    window = engine.rootObjects()[0]
    assert isinstance(window, QQuickWindow)
    view().setProperty("url", QUrl("data:text/html," + PAGE.decode()))
    QTimer.singleShot(4000, open_select)
    sys.exit(app.exec())
