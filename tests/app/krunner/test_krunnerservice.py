from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl

from kondor.app.instance.singleinstancemessage import SingleInstanceMessage
from kondor.app.krunner import krunnerservice
from kondor.app.krunner.krunnerservice import KRunnerService
from kondor.app.krunner.runnerreply import display_string
from kondor.app.windows.windowmanager import WindowManager
from tests.app.krunner.runnerfakes import FakeTab, FakeWindow
from tests.history.historyrows import add_visit, now_ms


class Recorder:
    def __init__(self) -> None:
        self.raised: list[tuple[QObject, bytes]] = []
        self.opened: list[SingleInstanceMessage] = []


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> Recorder:
    recorded = Recorder()
    monkeypatch.setattr(
        krunnerservice,
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

    signature, body = service.handle_call("Match", ("zebra",))  # type: ignore[misc]

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
    _, body = service.handle_call("Match", ("kde",))  # type: ignore[misc]

    assert body[0][0][:5] == ("tab-0", "Kde news", "internet-web-browser", 100, 1.0)


def test_actions_reply_is_empty(service: KRunnerService) -> None:
    assert service.handle_call("Actions", ()) == ("a(sss)", ([],))


def test_run_switches_to_the_tab_and_raises_its_window(
    service: KRunnerService, window: FakeWindow, recorder: Recorder
) -> None:
    service.handle_call("Match", ("qt.io",))
    service.handle_call("SetActivationToken", ("token",))

    service.handle_call("Run", ("tab-0", ""))

    assert window.model.current_index == 1
    assert recorder.raised == [(window, b"token")]


def test_run_on_a_closed_tab_opens_its_url(
    service: KRunnerService, window: FakeWindow, recorder: Recorder
) -> None:
    service.handle_call("Match", ("qt.io",))
    window.model.fakes.clear()

    service.handle_call("Run", ("tab-0", ""))

    assert [m.urls for m in recorder.opened] == [[QUrl("https://qt.io/")]]


def test_run_on_a_history_entry_opens_it_with_the_token(
    service: KRunnerService, window: FakeWindow, recorder: Recorder
) -> None:
    add_visit("https://hist.example/", "Zebra", now_ms())
    service.handle_call("Match", ("zebra",))
    service.handle_call("SetActivationToken", ("abc",))

    service.handle_call("Run", ("history-0", ""))

    assert [(m.urls, m.activation_token) for m in recorder.opened] == [
        ([QUrl("https://hist.example/")], b"abc")
    ]


def test_run_with_unknown_id_does_nothing(service: KRunnerService, recorder: Recorder) -> None:
    service.handle_call("Run", ("tab-9", ""))

    assert recorder.opened == [] and recorder.raised == []


def test_teardown_forgets_the_matches(service: KRunnerService, window: FakeWindow) -> None:
    service.handle_call("Match", ("kde",))

    service.handle_call("Teardown", ())

    assert service.last_matches == {}


def test_unknown_member_returns_none(service: KRunnerService) -> None:
    assert service.handle_call("Frobnicate", ()) is None


def test_display_string_hides_the_user_info() -> None:
    assert display_string(QUrl("https://user:secret@kde.org:8080/a")) == "https://kde.org:8080/a"
