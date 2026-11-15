from PySide6.QtQml import QQmlComponent, QQmlEngine

from kondor.app.windows.windowmanager import WindowManager
from tests.qmlsupport import load_component

STUB_WINDOW_QML = """
import QtQuick
Window {
    property bool privateWindow: false
    property var initialUrls: []
    property var initialTitles: []
    property int initialCurrentIndex: -1
    property var addedUrls: []
    property var openedPages: []
    function openUrlsInNewTabs(urls) { addedUrls = addedUrls.concat(urls.map(String)) }
    function openSettingsPage(pageId) { openedPages = openedPages.concat([pageId]) }
}
"""


class StubWindowManager(WindowManager):
    def __init__(self, engine: QQmlEngine) -> None:
        super().__init__()
        self.set_engine(engine)

    def load_component(self) -> QQmlComponent | None:
        if self._component is None:
            self._component = load_component(self._engine, STUB_WINDOW_QML)
        return self._component
