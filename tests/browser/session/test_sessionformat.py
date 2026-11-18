import pytest
from PySide6.QtCore import QUrl

from kondor.browser.session.sessionformat import from_json, to_json
from kondor.browser.session.sessionwindow import SessionTab, SessionWindow
from tests.qmlsupport import captured_messages

COMPACT_VERSION_TWO = (
    b'{"version":2,"windows":[{"currentIndex":1,"tabs":['
    b'{"title":"A","url":"https://a.example/"},{"title":"","url":"about:newtab"}]}]}'
)
VERSION_ONE = (
    b'{"version":1,"currentIndex":1,"tabs":['
    b'{"url":"https://a.example/","title":"A"},{"url":"https://b.example/","title":"B"}]}'
)


def sample_window() -> SessionWindow:
    return SessionWindow([SessionTab(QUrl("https://a.example/"), "A"), SessionTab(QUrl(), "")], 1)


def test_writes_the_compact_version_two_bytes() -> None:
    assert to_json([sample_window()]) == COMPACT_VERSION_TWO


def test_round_trips() -> None:
    windows = [sample_window(), SessionWindow([SessionTab(QUrl("https://b.example/"), "B")], 0)]
    assert from_json(to_json(windows)) == windows


def test_reads_the_version_one_format() -> None:
    first, second = QUrl("https://a.example/"), QUrl("https://b.example/")
    tabs = [SessionTab(first, "A"), SessionTab(second, "B")]
    assert from_json(VERSION_ONE) == [SessionWindow(tabs, 1)]


@pytest.mark.parametrize(
    ("json", "warning"),
    [
        (b"not json", "Kondor: ignoring invalid session file: "),
        (b'{"version":3,"windows":[]}', "Kondor: ignoring unsupported session file version"),
        (b'{"version":2,"windows":[{"currentIndex":0,"tabs":[]}]}', None),
    ],
    ids=["not json", "future version", "window without tabs"],
)
def test_ignores_invalid_and_future_files(json: bytes, warning: str | None) -> None:
    with captured_messages() as messages:
        assert from_json(json) == []
    if warning is not None:
        assert any(message.startswith(warning) for message in messages)


def test_reads_about_newtab_as_an_empty_url() -> None:
    json = b'{"version":2,"windows":[{"currentIndex":0,"tabs":[{"url":"about:newtab"}]}]}'
    assert from_json(json)[0].tabs[0].url.isEmpty()


def test_round_trips_agent_access_of_a_tab() -> None:
    tabs = [SessionTab(QUrl("https://a.example/"), "A", True, "Claude Code")]

    loaded = from_json(to_json([SessionWindow(tabs, 0)]))

    assert (loaded[0].tabs[0].has_agent_access, loaded[0].tabs[0].agent_name) == (
        True,
        "Claude Code",
    )


def test_a_tab_saved_without_agent_keys_has_no_access() -> None:
    saved = b'{"version":2,"windows":[{"currentIndex":0,"tabs":[{"url":"https://a.example/","title":"A"}]}]}'

    assert from_json(saved)[0].tabs[0].has_agent_access is False


def test_does_not_write_agent_keys_for_a_tab_without_access() -> None:
    saved = to_json([SessionWindow([SessionTab(QUrl("https://a.example/"), "A")], 0)])

    assert b"agent" not in saved
