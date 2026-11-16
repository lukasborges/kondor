from collections.abc import Callable, Iterator

import pytest
from PySide6.QtCore import QUrl

from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from kondor.browser.tabs.tabsleepscheduler import TabSleepScheduler
from kondor.core.settings.settings import Settings

pytestmark = pytest.mark.no_qt_log

MINUTE = 60.0
DEFAULT_LIMIT = 30 * MINUTE
MAKE_EXEMPT: dict[str, Callable[[TabModel, Tab], None]] = {
    "pinned": lambda model, tab: model.setPinned(model.indexOfTab(tab), True),
    "sleeping": lambda model, tab: tab.sleep.setSleeping(True),
    "newTabPage": lambda model, tab: tab.showNewTabPage(),
    "crashed": lambda model, tab: tab.setCrashed(True, "x", 1),
    "reader": lambda model, tab: tab.setReaderActive(True),
    "dev": lambda model, tab: tab.setDevToolsOpen(True),
}


class Rig:
    def __init__(self, model: TabModel, settings: Settings) -> None:
        self.model = model
        self.settings = settings
        self.now = 0.0
        self.scheduler = TabSleepScheduler(model, lambda: self.now)
        self.tab = model.addTab(False, QUrl("https://a.example"))
        model.addTab()
        assert self.tab is not None
        self.requests = 0
        self.tab.sleep.idleSleepRequested.connect(self._count)

    def _count(self) -> None:
        self.requests += 1

    def idle_for(self, seconds: float) -> None:
        self.now += seconds
        self.scheduler.check()


@pytest.fixture
def settings(qapp: object) -> Iterator[Settings]:
    stored = Settings.instance()
    stored.setProperty("tabSleepEnabled", True)
    stored.setProperty("tabSleepMinutes", 30)
    yield stored


@pytest.fixture
def rig(model: TabModel, settings: Settings) -> Rig:
    return Rig(model, settings)


def test_idle_background_tab_is_asked_after_the_limit(rig: Rig) -> None:
    rig.idle_for(DEFAULT_LIMIT - 1)
    assert rig.requests == 0
    rig.idle_for(1)
    assert rig.requests == 1


def test_current_tab_is_never_asked(rig: Rig) -> None:
    rig.model.setCurrentIndex(rig.model.indexOfTab(rig.tab))
    rig.idle_for(DEFAULT_LIMIT * 2)
    assert rig.requests == 0


@pytest.mark.parametrize("state", MAKE_EXEMPT)
def test_exempt_tab_is_never_asked(rig: Rig, state: str) -> None:
    MAKE_EXEMPT[state](rig.model, rig.tab)
    rig.idle_for(DEFAULT_LIMIT * 2)
    assert rig.requests == 0


def test_selecting_a_tab_resets_its_idle_time(rig: Rig) -> None:
    rig.idle_for(DEFAULT_LIMIT - 1)
    rig.model.setCurrentIndex(rig.model.indexOfTab(rig.tab))
    rig.model.setCurrentIndex(rig.model.count - 1)
    rig.idle_for(2)
    assert rig.requests == 0


def test_disabling_the_option_stops_requests(rig: Rig) -> None:
    rig.settings.setProperty("tabSleepEnabled", False)
    rig.idle_for(DEFAULT_LIMIT * 2)
    assert rig.requests == 0


def test_the_limit_follows_the_setting(rig: Rig) -> None:
    rig.settings.setProperty("tabSleepMinutes", 15)
    rig.idle_for(15 * MINUTE)
    assert rig.requests == 1
