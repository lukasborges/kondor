import json
from collections.abc import Iterator
from typing import Any

import pytest
from PySide6.QtCore import QFile, QIODevice, QUrl
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineScript
from pytestqt.qtbot import QtBot

pytestmark = pytest.mark.no_qt_log

TIMEOUT_MS = 10000
MAIN = QWebEngineScript.ScriptWorldId.MainWorld.value
APPLICATION = QWebEngineScript.ScriptWorldId.ApplicationWorld.value
PAGE = "<html><head><title>Page title</title></head><body></body></html>"
FAKE_CHANNEL = "window.__kondorChannel = Promise.resolve({});"
FAKE_ELEMENT = "{ paused: false, duration: Infinity, currentTime: 3, playbackRate: 1.5 }"
METADATA = (
    "navigator.mediaSession.metadata = new MediaMetadata({ title: 'Song', artist: 'Band',"
    " album: 'Record', artwork: [{ src: 'small.png', sizes: '96x96' },"
    " { src: '/big.png', sizes: '512x512' }, { src: 'mid.png', sizes: '256x256' }] });"
)
RECORD_ACTIONS = (
    "window.seen = []; document.addEventListener('kondor-media-actions',"
    " (e) => window.seen.push(e.detail));"
)
HANDLERS = (
    "window.calls = []; navigator.mediaSession.setActionHandler('seekto',"
    " (d) => window.calls.push(d)); navigator.mediaSession.setActionHandler('nexttrack',"
    " () => { throw new Error('page bug'); });"
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

    def evaluate(self, script: str, world: int = MAIN) -> Any:
        results: list[Any] = []
        self.page.runJavaScript(script, world, results.append)
        self._qtbot.waitUntil(lambda: bool(results), timeout=TIMEOUT_MS)
        return results[0]

    def load(self) -> None:
        with self._qtbot.waitSignal(self.page.loadFinished, timeout=TIMEOUT_MS):
            self.page.setHtml(PAGE, QUrl("http://localhost"))

    def request(self, action: str, seek_time: float = 0) -> None:
        detail = json.dumps(json.dumps({"action": action, "seekTime": seek_time}))
        event = f"new CustomEvent('kondor-media-action', {{ detail: {detail} }})"
        self.evaluate(f"document.dispatchEvent({event}); 0")

    def report(self) -> dict[str, Any]:
        self.evaluate(FAKE_CHANNEL, APPLICATION)
        self.evaluate(read_script(":/scripts/mediawatch.js"), APPLICATION)
        raw = self.evaluate(
            f"JSON.stringify(window.__kondorMediaWatch.buildReport({FAKE_ELEMENT}))", APPLICATION
        )
        return json.loads(raw)  # type: ignore[no-any-return]


@pytest.fixture
def script_page(qtbot: QtBot, staged_resources: None) -> Iterator[ScriptPage]:
    page = ScriptPage(qtbot)
    page.load()
    yield page
    page.page.deleteLater()


@pytest.fixture
def shim_page(script_page: ScriptPage) -> ScriptPage:
    script_page.evaluate(RECORD_ACTIONS)
    script_page.evaluate(read_script(":/scripts/mediasession.js"))
    script_page.evaluate(HANDLERS)
    return script_page


def test_shim_announces_the_page_actions(shim_page: ScriptPage) -> None:
    seen = shim_page.evaluate("JSON.stringify(window.seen)")

    assert json.loads(json.loads(seen)[-1]) == ["seekto", "nexttrack"]


def test_action_request_calls_the_page_handler_with_the_seek_time(shim_page: ScriptPage) -> None:
    shim_page.request("seekto", 12.5)

    assert shim_page.evaluate("JSON.stringify(window.calls)") == (
        '[{"action":"seekto","seekTime":12.5}]'
    )


def test_a_throwing_handler_does_not_break_later_calls(shim_page: ScriptPage) -> None:
    shim_page.request("nexttrack")
    shim_page.request("seekto", 3)

    assert json.loads(shim_page.evaluate("JSON.stringify(window.calls)"))[0]["seekTime"] == 3  # noqa: PLR2004


def test_the_page_sees_no_new_window_property(script_page: ScriptPage) -> None:
    names = "JSON.stringify(Object.getOwnPropertyNames(window).sort())"
    before = script_page.evaluate(names)

    script_page.evaluate(read_script(":/scripts/mediasession.js"))

    assert script_page.evaluate(names) == before


def test_report_uses_the_media_session_metadata(script_page: ScriptPage) -> None:
    script_page.evaluate(METADATA)

    report = script_page.report()

    assert (report["title"], report["artist"], report["album"]) == ("Song", "Band", "Record")
    assert report["artworkUrl"] == "http://localhost/big.png"
    assert (report["duration"], report["position"], report["rate"]) == (0, 3, 1.5)  # noqa: PLR2004


def test_report_falls_back_to_the_document_title_and_host(script_page: ScriptPage) -> None:
    report = script_page.report()

    assert (report["title"], report["artist"], report["artworkUrl"]) == (
        "Page title",
        "localhost",
        "",
    )
