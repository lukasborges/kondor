from collections.abc import Iterator

import pytest
from PySide6.QtCore import QFile, QIODevice, QUrl
from PySide6.QtTest import QTest
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from pytestqt.qtbot import QtBot

pytestmark = pytest.mark.no_qt_log

ORIGIN = "http://localhost"
TIMEOUT_MS = 10000
FAKE_BRIDGE = (
    "window.__kondorChannel = Promise.resolve({ kondorPasswords: {"
    "  credentialsFor: (o, cb) => { window.__lookups = (window.__lookups || 0) + 1; cb([]); },"
    "  formSubmitted: () => {},"
    "  credentialsChanged: { connect: () => {} },"
    "  fillRequested: { connect: (f) => { window.__fill = f; } } } });"
)
USERNAME_STEP = (
    "<form><input type='text' name='q'><input type='email' name='who'><button>Next</button></form>"
)
PASSWORD_STEP = "<form><input type='text' name='user'><input type='password' name='pw'></form>"
NO_USERNAME_FIELD = "<form><input type='number' name='age'></form>"
LATER_FIELD = (
    "document.body.insertAdjacentHTML('beforeend', \"<input type='email' name='who'>\"); 0"
)
MORE_CONTENT = "document.body.insertAdjacentHTML('beforeend', '<p>more</p>'); 0"
SETTLE_MS = 600


def read_script(path: str) -> str:
    file = QFile(path)
    assert file.open(QIODevice.OpenModeFlag.ReadOnly)
    return bytes(file.readAll().data()).decode()


class FillPage:
    def __init__(self, qtbot: QtBot) -> None:
        self._qtbot = qtbot
        self._profile = QWebEngineProfile()
        self.page = QWebEnginePage(self._profile)

    def evaluate(self, script: str) -> object:
        results: list[object] = []
        self.page.runJavaScript(script, results.append)
        self._qtbot.waitUntil(lambda: bool(results), timeout=TIMEOUT_MS)
        return results[0]

    def load(self, body: str) -> None:
        with self._qtbot.waitSignal(self.page.loadFinished, timeout=TIMEOUT_MS):
            self.page.setHtml(body, QUrl(ORIGIN))
        self.evaluate(FAKE_BRIDGE)
        for name in ("usernamefield", "fieldvalue", "newpasswordfield", "passwords"):
            self.evaluate(read_script(f":/scripts/{name}.js"))
        self._qtbot.waitUntil(
            lambda: self.evaluate("typeof window.__fill === 'function'") is True,
            timeout=TIMEOUT_MS,
        )

    def request_fill(self) -> None:
        self.evaluate(f"window.__fill('{ORIGIN}', 'ada@example.com', 'secret')")

    def value_of(self, name: str) -> object:
        return self.evaluate(f"document.querySelector('[name={name}]').value")

    def lookup_count(self) -> object:
        return self.evaluate("window.__lookups || 0")


@pytest.fixture
def fill_page(qapp: object, staged_resources: None, qtbot: QtBot) -> Iterator[FillPage]:
    page = FillPage(qtbot)
    yield page
    page.page.deleteLater()


def test_fills_username_on_username_only_step(fill_page: FillPage) -> None:
    fill_page.load(USERNAME_STEP)
    fill_page.request_fill()
    assert fill_page.value_of("who") == "ada@example.com"
    assert fill_page.value_of("q") == ""


def test_fills_username_and_password_on_password_step(fill_page: FillPage) -> None:
    fill_page.load(PASSWORD_STEP)
    fill_page.request_fill()
    assert fill_page.value_of("user") == "ada@example.com"
    assert fill_page.value_of("pw") == "secret"


def test_fills_nothing_without_username_field(fill_page: FillPage) -> None:
    fill_page.load(NO_USERNAME_FIELD)
    fill_page.request_fill()
    assert fill_page.value_of("age") == ""


def test_looks_up_credentials_on_username_only_page(fill_page: FillPage) -> None:
    fill_page.load(USERNAME_STEP)
    assert fill_page.lookup_count() == 1


def test_does_not_look_up_credentials_without_login_field(fill_page: FillPage) -> None:
    fill_page.load(NO_USERNAME_FIELD)
    QTest.qWait(SETTLE_MS)
    assert fill_page.lookup_count() == 0


def test_looks_up_credentials_once_when_field_appears_later(
    fill_page: FillPage, qtbot: QtBot
) -> None:
    fill_page.load(NO_USERNAME_FIELD)
    fill_page.evaluate(LATER_FIELD)
    qtbot.waitUntil(lambda: fill_page.lookup_count() == 1, timeout=5000)
    fill_page.evaluate(MORE_CONTENT)
    QTest.qWait(SETTLE_MS)
    assert fill_page.lookup_count() == 1
