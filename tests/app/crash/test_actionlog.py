import gc
import weakref
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl

from kondor.app.crash.actionlog import MAX_ENTRIES, ActionLog


class FakeTab(QObject):
    def __init__(self, is_private: bool) -> None:
        super().__init__()
        self.setProperty("isPrivate", is_private)


log_path_of: "weakref.WeakKeyDictionary[ActionLog, Path]" = weakref.WeakKeyDictionary()


@pytest.fixture
def log(tmp_path: Path) -> ActionLog:
    action_log = ActionLog(clock=lambda: "10:00:00")
    action_log.start(tmp_path / "actions.log")
    log_path_of[action_log] = tmp_path / "actions.log"
    return action_log


def written(log: ActionLog) -> list[str]:
    return (log_path_of[log]).read_text().splitlines()


def test_keepsOnlyTheLastFortyEntries(log: ActionLog) -> None:
    for number in range(MAX_ENTRIES + 5):
        log.record(f"event {number}")
    assert len(written(log)) == MAX_ENTRIES
    assert written(log)[-1] == "10:00:00 event 44"


def test_recordsNothingBeforeStart() -> None:
    ActionLog().record("event")


def test_dropsEventsOfPrivateTabs(log: ActionLog) -> None:
    private = FakeTab(True)
    log.pageEvent(private, "context menu opened")
    log.navigationStarted(private, QUrl("https://secret.example/page"))
    log.navigationFailed(private, 3)
    assert written(log) == []


def test_recordsEventsOfNormalTabs(log: ActionLog) -> None:
    log.pageEvent(FakeTab(False), "context menu opened")
    assert written(log) == ["10:00:00 context menu opened"]


def test_labelsNavigationAsSameOrCrossSite(log: ActionLog) -> None:
    tab = FakeTab(False)
    log.navigationStarted(tab, QUrl("https://www.example.org/a"))
    log.navigationStarted(tab, QUrl("https://docs.example.org/b"))
    log.navigationStarted(tab, QUrl("https://other.net/"))
    assert [line.split(" ", 1)[1] for line in written(log)] == [
        "navigation started cross-site",
        "navigation started same-site",
        "navigation started cross-site",
    ]


def test_neverWritesHostsOrUrls(log: ActionLog) -> None:
    tab = FakeTab(False)
    log.navigationStarted(tab, QUrl("https://secret.example/page?q=1"))
    log.navigationFinished(tab)
    assert "secret" not in "\n".join(written(log))


def test_windowEventsSkipPrivateWindows(log: ActionLog) -> None:
    log.record_unless_private(True, "window opened")
    log.record_unless_private(False, "window opened")
    assert len(written(log)) == 1


def test_forgetsClosedTabs(log: ActionLog) -> None:
    tab = FakeTab(False)
    log.navigationStarted(tab, QUrl("https://example.org/"))
    reference = weakref.ref(tab)
    del tab
    gc.collect()
    assert reference() is None
