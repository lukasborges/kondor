import json
from typing import Any

import pytest
from PySide6.QtCore import QFile, QIODevice, QUrl
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineScript
from pytestqt.qtbot import QtBot

pytestmark = pytest.mark.no_qt_log

TIMEOUT_MS = 10000
APPLICATION = QWebEngineScript.ScriptWorldId.ApplicationWorld.value
FAKE_CHANNEL = (
    "window.reports = [];"
    " window.__kondorChannel = Promise.resolve({ kondorAgentPointer:"
    " { report: (type, x, y) => window.reports.push([type, x, y]) } });"
)
DISPATCH_CLICK = (
    "document.body.dispatchEvent(new PointerEvent('pointerdown',"
    " { clientX: 30, clientY: 40, bubbles: true })); 0"
)


def read_script(path: str) -> str:
    file = QFile(path)
    assert file.open(QIODevice.OpenModeFlag.ReadOnly)
    return bytes(file.readAll().data()).decode()


class ScriptPage:
    def __init__(self, qtbot: QtBot) -> None:
        self._qtbot = qtbot
        self._profile = QWebEngineProfile()
        self.page = QWebEnginePage(self._profile)

    def evaluate(self, script: str) -> Any:
        results: list[Any] = []
        self.page.runJavaScript(script, APPLICATION, results.append)
        self._qtbot.waitUntil(lambda: bool(results), timeout=TIMEOUT_MS)
        return results[0]

    def load_with_script(self) -> None:
        with self._qtbot.waitSignal(self.page.loadFinished, timeout=TIMEOUT_MS):
            self.page.setHtml("<html><body></body></html>", QUrl("http://localhost"))
        self.evaluate(FAKE_CHANNEL)
        self.evaluate(read_script(":/scripts/agentpointer.js") + "; 0")
        self.evaluate("window.__kondorChannel.then(() => 0)")

    def reports(self) -> list[list[Any]]:
        return json.loads(self.evaluate("JSON.stringify(window.reports)"))  # type: ignore[no-any-return]


@pytest.fixture
def page(qapp: object, staged_resources: None, qtbot: QtBot) -> ScriptPage:
    scripted = ScriptPage(qtbot)
    scripted.load_with_script()
    return scripted


def test_reports_a_press_at_once(page: ScriptPage) -> None:
    page.evaluate(DISPATCH_CLICK)
    assert page.reports() == [["pointerdown", 30, 40]]
