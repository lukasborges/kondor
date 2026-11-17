from pathlib import Path
from typing import Any

import pytest
from PySide6.QtCore import QObject, QUrl, qInstallMessageHandler

from kondor.app.instance.singleinstancemessage import SingleInstanceMessage
from kondor.app.krunner.krunnerservice import KRunnerService
from kondor.app.krunner.runnerreply import display_string
from kondor.app.windows import windowtabs
from kondor.app.windows.windowmanager import WindowManager
from kondor.core.dbus.buscall import BusCall
from tests.app.krunner.runnerfakes import FakeTab, FakeWindow
from tests.history.historyrows import add_visit, now_ms


def ask(service: KRunnerService, member: str, body: tuple[Any, ...]) -> tuple[str, tuple[Any, ...]]:
    reply = service.handle_call(BusCall("/KRunner", "org.kde.krunner1", member, body))
    assert reply is not None
    return reply.signature, reply.body


class Recorder:
    def __init__(self) -> None:
        self.raised: list[tuple[QObject, bytes]] = []
        self.opened: list[SingleInstanceMessage] = []


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> Recorder:
    recorded = Recorder()
    monkeypatch.setattr(
        windowtabs,
        "raise_window",
        lambda window, token: recorded.raised.append((window, token)),
    )
    monkeypatch.setattr(
        WindowManager, "handle_single_instance_message", lambda self, m: recorded.opened.append(m)
    )
    return recorded


@pytest.fixture
def window(monkeypatch: pytest.MonkeyPatch, fresh_database: Path) -> FakeWindow:
    fake = FakeWindow([FakeTab("Kde news", "https://kde.org/"), FakeTab("Qt", "https://qt.io/")])
    monkeypatch.setattr(WindowManager, "windows", lambda self: [fake])
    return fake


@pytest.fixture
def service() -> KRunnerService:
    return KRunnerService()


def test_match_replies_with_runner_structs(service: KRunnerService, window: FakeWindow) -> None:
    add_visit("https://hist.example/", "Zebra history", now_ms())

    signature, body = ask(service, "Match", ("zebra",))

    (history,) = body[0]
    assert signature == "a(sssida{sv})"
    assert history[:4] == ("history-0", "Zebra history", "view-history", 50)
    assert history[5] == {
        "subtext": ("s", "https://hist.example/"),
        "urls": ("as", ["https://hist.example/"]),
        "actions": ("as", []),
    }


def test_match_lists_open_tabs_first_with_full_relevance(
    service: KRunnerService, window: FakeWindow
) -> None:
    _, body = ask(service, "Match", ("kde",))

    assert body[0][0][:5] == ("tab-0", "Kde news", "internet-web-browser", 100, 1.0)


def test_actions_reply_is_empty(service: KRunnerService) -> None:
    assert ask(service, "Actions", ()) == ("a(sss)", ([],))


def test_run_switches_to_the_tab_and_raises_its_window(
    service: KRunnerService, window: FakeWindow, recorder: Recorder
) -> None:
    ask(service, "Match", ("qt.io",))
    ask(service, "SetActivationToken", ("token",))

    ask(service, "Run", ("tab-0", ""))

    assert window.model.current_index == 1
    assert recorder.raised == [(window, b"token")]


def test_run_on_a_closed_tab_opens_its_url(
    service: KRunnerService, window: FakeWindow, recorder: Recorder
) -> None:
    ask(service, "Match", ("qt.io",))
    window.model.fakes.clear()

    ask(service, "Run", ("tab-0", ""))

    assert [m.urls for m in recorder.opened] == [[QUrl("https://qt.io/")]]


def test_run_on_a_history_entry_opens_it_with_the_token(
    service: KRunnerService, window: FakeWindow, recorder: Recorder
) -> None:
    add_visit("https://hist.example/", "Zebra", now_ms())
    ask(service, "Match", ("zebra",))
    ask(service, "SetActivationToken", ("abc",))

    ask(service, "Run", ("history-0", ""))

    assert [(m.urls, m.activation_token) for m in recorder.opened] == [
        ([QUrl("https://hist.example/")], b"abc")
    ]


def test_run_with_unknown_id_does_nothing(service: KRunnerService, recorder: Recorder) -> None:
    ask(service, "Run", ("tab-9", ""))

    assert recorder.opened == [] and recorder.raised == []


def test_teardown_forgets_the_matches(service: KRunnerService, window: FakeWindow) -> None:
    ask(service, "Match", ("kde",))

    ask(service, "Teardown", ())

    assert service.last_matches == {}


def test_unknown_member_returns_none(service: KRunnerService) -> None:
    assert service.handle_call(BusCall("/KRunner", "org.kde.krunner1", "Frobnicate", ())) is None


def test_display_string_hides_the_user_info() -> None:
    assert display_string(QUrl("https://user:secret@kde.org:8080/a")) == "https://kde.org:8080/a"


def test_second_instance_logs_that_another_answers(qapp: object) -> None:
    first, second = KRunnerService(), KRunnerService()
    seen: list[tuple[str | None, str]] = []

    def record(message_type: object, context: object, message: str) -> None:
        seen.append((getattr(context, "category", None), message))

    previous = qInstallMessageHandler(record)
    try:
        started = (first.start(), second.start())
    finally:
        qInstallMessageHandler(previous)
        first.stop()
        second.stop()
    assert started == (True, False)
    assert seen == [("kondor.krunner", "Kondor: another instance answers KRunner")]
