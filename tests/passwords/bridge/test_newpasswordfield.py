from collections.abc import Iterator

import pytest
from PySide6.QtCore import QFile, QIODevice, QUrl
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from pytestqt.qtbot import QtBot

pytestmark = pytest.mark.no_qt_log

TIMEOUT_MS = 10000
NEW_PASSWORD = "<input type=password id=a autocomplete=new-password>"
LOGIN = "<form><input type=text name=user><input type=password id=a name=password></form>"
SIGN_UP = "<form><input type=password id=a name=pw><input type=password id=b name=again></form>"
CHANGE = (
    "<form><input type=password id=a><input type=password id=b><input type=password id=c></form>"
)
SHORT = "<input type=password id=a maxlength=6>"
LIMITED = "<input type=password id=a autocomplete=new-password minlength=30 maxlength=40>"
RAISED_LENGTH = 30
PATTERNED = "<input type=password id=a pattern='[a-z]+'>"


class ScriptPage:
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
            self.page.setHtml(body, QUrl("http://localhost"))
        file = QFile(":/scripts/newpasswordfield.js")
        assert file.open(QIODevice.OpenModeFlag.ReadOnly)
        self.evaluate(bytes(file.readAll().data()).decode())

    def kind_of(self, field_id: str) -> object:
        return self.evaluate(
            f"window.__kondorNewPasswordFields.kindOf(document.getElementById('{field_id}'))"
        )


@pytest.fixture
def script_page(qapp: object, staged_resources: None, qtbot: QtBot) -> Iterator[ScriptPage]:
    page = ScriptPage(qtbot)
    yield page
    page.page.deleteLater()


def test_autocomplete_marks_a_new_password(script_page: ScriptPage) -> None:
    script_page.load(NEW_PASSWORD)
    assert script_page.kind_of("a") == "new"


def test_plain_login_form_is_a_password(script_page: ScriptPage) -> None:
    script_page.load(LOGIN)
    assert script_page.kind_of("a") == "password"


def test_both_fields_of_a_sign_up_form_are_new(script_page: ScriptPage) -> None:
    script_page.load(SIGN_UP)
    assert (script_page.kind_of("a"), script_page.kind_of("b")) == ("new", "new")


def test_change_password_form_has_a_current_and_two_new_fields(script_page: ScriptPage) -> None:
    script_page.load(CHANGE)
    kinds = [script_page.kind_of(field_id) for field_id in "abc"]
    assert kinds == ["password", "new", "new"]


def test_too_short_field_is_ignored(script_page: ScriptPage) -> None:
    script_page.load(SHORT)
    assert script_page.kind_of("a") == ""


def test_confirmation_is_the_other_new_field(script_page: ScriptPage) -> None:
    script_page.load(SIGN_UP)
    script = "window.__kondorNewPasswordFields.confirmationOf(document.getElementById('a')).id"
    assert script_page.evaluate(script) == "b"


def test_rules_follow_minlength_and_maxlength(script_page: ScriptPage) -> None:
    script_page.load(LIMITED)
    script = "window.__kondorNewPasswordFields.rulesOf(document.getElementById('a')).length"
    assert script_page.evaluate(script) == RAISED_LENGTH


def test_pattern_is_checked_against_the_whole_value(script_page: ScriptPage) -> None:
    script_page.load(PATTERNED)
    check = "window.__kondorNewPasswordFields.matchesPattern(document.getElementById('a'), '%s')"
    assert script_page.evaluate(check % "abc") is True
    assert script_page.evaluate(check % "abc1") is False
