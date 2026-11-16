import pytest
from shiboken6 import delete

from kondor.browser.media.mediastate import MediaState
from kondor.browser.media.mediatabs import MediaTabs
from kondor.browser.tabs.features.tabmedia import TabMedia
from tests.browser.media.mediafakes import PAUSED, PLAYING

CHANGES = 4


@pytest.fixture
def tabs(fresh_media_tabs: MediaTabs) -> MediaTabs:
    return fresh_media_tabs


def test_a_started_tab_becomes_current(tabs: MediaTabs) -> None:
    media = TabMedia()

    media.apply(PLAYING)

    assert tabs.current is media


def test_media_that_never_played_is_never_current(tabs: MediaTabs) -> None:
    media = TabMedia()

    media.apply(PAUSED)

    assert tabs.current is None


def test_a_newer_start_takes_over(tabs: MediaTabs) -> None:
    first, second = TabMedia(), TabMedia()
    first.apply(PLAYING)

    second.apply(PLAYING)

    assert tabs.current is second


def test_pausing_keeps_the_current_tab(tabs: MediaTabs) -> None:
    first, second = TabMedia(), TabMedia()
    first.apply(PLAYING)
    second.apply(PLAYING)

    second.apply(PAUSED)

    assert tabs.current is second


def test_losing_media_falls_back_to_the_next(tabs: MediaTabs) -> None:
    first, second = TabMedia(), TabMedia()
    first.apply(PLAYING)
    second.apply(PLAYING)

    second.apply(MediaState())

    assert tabs.current is first


def test_a_destroyed_tab_falls_back_to_the_next(tabs: MediaTabs) -> None:
    first, second = TabMedia(), TabMedia()
    first.apply(PLAYING)
    second.apply(PLAYING)

    delete(second)

    assert tabs.current is first


def test_current_changed_is_emitted_once_per_change(tabs: MediaTabs) -> None:
    changes: list[int] = []
    tabs.currentChanged.connect(lambda: changes.append(1))
    first, second = TabMedia(), TabMedia()

    first.apply(PLAYING)
    first.apply(PAUSED)
    second.apply(PLAYING)
    second.apply(MediaState())
    first.apply(MediaState())

    assert len(changes) == CHANGES
