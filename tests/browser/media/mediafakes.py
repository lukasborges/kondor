from collections.abc import Iterator
from dataclasses import replace

import pytest
from PySide6.QtCore import QUrl

from kondor.browser.media.mediastate import MediaState
from kondor.browser.media.mediatabs import MediaTabs

PLAYING = MediaState(
    has_media=True,
    is_playing=True,
    title="Song",
    artist="Band",
    album="Record",
    artwork_url=QUrl("https://example.com/cover.png"),
    duration=200.0,
    position=10.0,
    actions=frozenset({"nexttrack", "previoustrack", "seekto"}),
)
PAUSED = replace(PLAYING, is_playing=False)


@pytest.fixture
def fresh_media_tabs(qapp: object) -> Iterator[MediaTabs]:
    previous = MediaTabs._instance
    MediaTabs._instance = MediaTabs()
    yield MediaTabs._instance
    MediaTabs._instance = previous
