from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot
from shiboken6 import delete

from kondor.browser.session.sessionmanager import SessionManager, session_file_path
from kondor.browser.tabs.tabmodel import TabModel

pytestmark = pytest.mark.no_qt_log

AUTOSAVE_WAIT_MS = 3000


@pytest.fixture
def session(qapp: object, isolated_profile: object) -> Iterator[SessionManager]:
    manager = SessionManager.instance()
    manager._models.clear()
    session_file_path().unlink(missing_ok=True)
    yield manager
    manager._models.clear()


def window_with(*names: str) -> TabModel:
    window = TabModel()
    for name in names:
        window.addTab(False, QUrl(f"https://{name}.example/"))
    return window


def private_window() -> TabModel:
    window = TabModel()
    window.privateTabs = True
    window.addTab(True, QUrl("https://private.example/"))
    return window


def write_session_file(content: bytes) -> None:
    session_file_path().write_bytes(content)


def test_saves_every_normal_window(session: SessionManager) -> None:
    first, second = window_with("one"), window_with("two", "three")
    session.save(first)
    session.save(second)
    windows = session.saved_windows()
    assert [len(window.tabs) for window in windows] == [1, 2]
    assert windows[0].tabs[0].url == QUrl("https://one.example/")
    assert windows[1].current_index == 1
    assert windows[1].tabs[1].url == QUrl("https://three.example/")


def test_keeps_the_session_when_only_private_windows_remain(session: SessionManager) -> None:
    normal = window_with("example")
    session.save(normal)
    closing_private = private_window()
    delete(normal)
    session.save(closing_private)
    windows = session.saved_windows()
    assert len(windows) == 1
    assert windows[0].tabs[0].url == QUrl("https://example.example/")


def test_reads_the_version_one_format(session: SessionManager) -> None:
    write_session_file(
        b'{"version":1,"currentIndex":1,"tabs":['
        b'{"url":"https://a.example/","title":"A"},{"url":"about:newtab","title":""}]}'
    )
    windows = session.saved_windows()
    assert len(windows) == 1
    assert windows[0].current_index == 1
    assert windows[0].tabs[0].title == "A"
    assert windows[0].tabs[1].url.isEmpty()


@pytest.mark.parametrize(
    "content",
    [
        b"not json",
        b'{"version":4,"windows":[{"currentIndex":0,"tabs":[{"url":"https://a.example/"}]}]}',
        b'{"version":2,"windows":[{"currentIndex":0,"tabs":[]}]}',
    ],
    ids=["invalid", "future", "empty-window"],
)
def test_ignores_invalid_and_future_files(session: SessionManager, content: bytes) -> None:
    write_session_file(content)
    assert session.saved_windows() == []


def test_saves_new_tab_page_as_about_new_tab(session: SessionManager) -> None:
    model = TabModel()
    model.addTab()
    session.save(model)
    assert b'"url":"about:newtab"' in session_file_path().read_bytes()
    assert session.saved_windows()[0].tabs[0].url.isEmpty()


def test_private_window_writes_no_session(session: SessionManager) -> None:
    session.save(private_window())
    assert not session_file_path().exists()


def test_private_tab_of_a_normal_window_is_not_saved(session: SessionManager) -> None:
    model = window_with("normal")
    model.addTab(True, QUrl("https://private.example/"))
    session.save(model)
    urls = [tab.url for tab in session.saved_windows()[0].tabs]
    assert urls == [QUrl("https://normal.example/")]


def test_url_change_schedules_a_save(session: SessionManager, qtbot: QtBot) -> None:
    model = window_with("before")
    session.watch(model)
    model.currentTab.setUrl(QUrl("https://after.example/"))
    qtbot.waitUntil(session_file_path().exists, timeout=AUTOSAVE_WAIT_MS)
    assert session.saved_windows()[0].tabs[0].url == QUrl("https://after.example/")


def test_destroyed_model_is_forgotten(session: SessionManager) -> None:
    kept, destroyed = window_with("kept"), window_with("gone")
    session.watch(kept)
    session.watch(destroyed)
    delete(destroyed)
    QTest.qWait(0)
    session.save_now()
    assert [window.tabs[0].url for window in session.saved_windows()] == [
        QUrl("https://kept.example/")
    ]


def test_session_file_is_inside_the_isolated_profile(
    session: SessionManager, isolated_profile: Path
) -> None:
    assert isolated_profile in session_file_path().parents
