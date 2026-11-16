import json
from collections.abc import Iterator

import pytest
from PySide6.QtCore import QFile, QIODevice, QUrl
from PySide6.QtTest import QTest
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from pytestqt.qtbot import QtBot

pytestmark = pytest.mark.no_qt_log

TIMEOUT_MS = 10000
SETTLE_MS = 200
FAKE_BRIDGE = """
window.__calls = [];
window.__kondorChannel = Promise.resolve({ kondorPasswords: {
  passwordFieldFocused: (field) => window.__calls.push(["focused", field.kind, field.offer]),
  passwordFieldLeft: () => window.__calls.push(["left"]),
  generatePassword: (rules, done) => done(rules.useSymbols ? "Abcdefghij1!" : "Abcdefghij12"),
  generatedPasswordFilled: (origin, value) => window.__calls.push(["filled", value]),
  generateRequested: { connect: (f) => { window.__generate = f; } } } });
"""
SIGN_UP = "<form><input id=a type=password name=pw><input id=b type=password name=again></form>"
PATTERNED = (
    "<input id=a type=password autocomplete=new-password maxlength=12 pattern='[A-Za-z0-9]+'>"
)


class FlowPage:
    def __init__(self, qtbot: QtBot) -> None:
        self._qtbot = qtbot
        self._profile = QWebEngineProfile()
        self.page = QWebEnginePage(self._profile)

    def evaluate(self, script: str) -> object:
        results: list[object] = []
        self.page.runJavaScript(script, results.append)
        self._qtbot.waitUntil(lambda: bool(results), timeout=TIMEOUT_MS)
        return results[0]

    def run_resource(self, name: str) -> None:
        file = QFile(f":/scripts/{name}.js")
        assert file.open(QIODevice.OpenModeFlag.ReadOnly)
        self.evaluate(bytes(file.readAll().data()).decode())

    def load(self, body: str) -> None:
        with self._qtbot.waitSignal(self.page.loadFinished, timeout=TIMEOUT_MS):
            self.page.setHtml(body, QUrl("http://localhost"))
        self.evaluate(FAKE_BRIDGE)
        for name in ("fieldvalue", "newpasswordfield", "newpassword"):
            self.run_resource(name)
        self._qtbot.waitUntil(
            lambda: self.evaluate("typeof window.__generate === 'function'") is True,
            timeout=TIMEOUT_MS,
        )

    def focus(self, field_id: str) -> None:
        script = "{ const el = document.getElementById('%s');"
        script += "el.dispatchEvent(new FocusEvent('focusin', { bubbles: true })); } 0"
        self.evaluate(script % field_id)

    def value_of(self, field_id: str) -> object:
        return self.evaluate(f"document.getElementById('{field_id}').value")

    def calls(self) -> list[list[object]]:
        calls: list[list[object]] = json.loads(str(self.evaluate("JSON.stringify(window.__calls)")))
        return calls


@pytest.fixture
def flow_page(qapp: object, staged_resources: None, qtbot: QtBot) -> Iterator[FlowPage]:
    page = FlowPage(qtbot)
    yield page
    page.page.deleteLater()


def test_focusing_an_empty_new_field_offers_the_suggestion(flow_page: FlowPage) -> None:
    flow_page.load(SIGN_UP)
    flow_page.focus("a")
    assert flow_page.calls() == [["focused", "new", True]]


def test_generating_fills_the_field_and_its_confirmation(flow_page: FlowPage) -> None:
    flow_page.load(SIGN_UP)
    flow_page.focus("a")
    flow_page.evaluate("window.__generate(); 0")
    QTest.qWait(SETTLE_MS)
    assert flow_page.value_of("a") == flow_page.value_of("b") != ""
    assert flow_page.calls()[-1] == ["left"]


def test_generated_value_respects_maxlength_and_pattern(flow_page: FlowPage) -> None:
    flow_page.load(PATTERNED)
    flow_page.focus("a")
    flow_page.evaluate("window.__generate(); 0")
    QTest.qWait(SETTLE_MS)
    assert flow_page.value_of("a") == "Abcdefghij12"


def test_dismissed_field_is_not_offered_again(flow_page: FlowPage) -> None:
    flow_page.load(SIGN_UP)
    flow_page.focus("a")
    flow_page.evaluate("document.getElementById('a').dispatchEvent(new Event('input')); 0")
    flow_page.focus("b")
    flow_page.focus("a")
    offers = [call[2] for call in flow_page.calls() if call[0] == "focused"]
    assert offers[-1] is False
