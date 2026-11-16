from dataclasses import replace

import pytest
from pytestqt.qtbot import QtBot

from kondor.browser.tabs.features.tabmedia import TabMedia
from tests.browser.media.mediafakes import PAUSED, PLAYING, fresh_media_tabs

__all__ = ["fresh_media_tabs"]


TWO_FLIPS = 2
EXTRAPOLATED = 20.0
PAUSED_POSITION = 10.0


class Clock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def media(fresh_media_tabs: object, clock: Clock) -> TabMedia:
    return TabMedia(clock=clock)


def count(signal: object) -> list[int]:
    calls: list[int] = []
    signal.connect(lambda: calls.append(1))  # type: ignore[attr-defined]
    return calls


def test_apply_emits_changed_for_a_new_state(media: TabMedia) -> None:
    changed = count(media.changed)

    media.apply(PLAYING)
    media.apply(PLAYING)

    assert len(changed) == 1


def test_position_alone_does_not_emit_changed(media: TabMedia) -> None:
    media.apply(PLAYING)
    changed = count(media.changed)

    media.apply(replace(PLAYING, position=50.0))

    assert changed == []


def test_playing_changed_follows_the_playing_flag(media: TabMedia) -> None:
    playing = count(media.playingChanged)

    media.apply(PLAYING)
    media.apply(PAUSED)
    media.apply(PAUSED)

    assert len(playing) == TWO_FLIPS


def test_seeked_is_emitted_for_seeked_reports(media: TabMedia) -> None:
    seeked = count(media.seeked)

    media.apply(replace(PLAYING, was_seeked=True))

    assert len(seeked) == 1


def test_clear_goes_back_to_the_empty_state(media: TabMedia) -> None:
    media.apply(PLAYING)

    media.clear()

    assert not media.hasMedia and not media.isPlaying


def test_position_is_extrapolated_while_playing(media: TabMedia, clock: Clock) -> None:
    media.apply(replace(PLAYING, rate=2.0))
    clock.now += 5

    assert media.current_position() == EXTRAPOLATED


def test_position_is_clamped_to_the_duration(media: TabMedia, clock: Clock) -> None:
    media.apply(PLAYING)
    clock.now += 1000

    assert media.current_position() == PLAYING.duration


def test_position_stays_when_paused(media: TabMedia, clock: Clock) -> None:
    media.apply(PAUSED)
    clock.now += 30

    assert media.current_position() == PAUSED_POSITION


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("play", ("play", 0.0)),
        ("pause", ("pause", 0.0)),
        ("stop", ("stop", 0.0)),
        ("next", ("nexttrack", 0.0)),
        ("previous", ("previoustrack", 0.0)),
    ],
)
def test_commands_emit_their_action(
    media: TabMedia, command: str, expected: tuple[str, float]
) -> None:
    seen: list[tuple[str, float]] = []
    media.actionRequested.connect(lambda action, seconds: seen.append((action, seconds)))

    getattr(media, command)()

    assert seen == [expected]


def test_seek_to_emits_the_seconds(media: TabMedia, qtbot: QtBot) -> None:
    with qtbot.waitSignal(media.actionRequested) as blocker:
        media.seekTo(42.5)

    assert tuple(blocker.args or ()) == ("seekto", 42.5)


def test_toggle_pauses_when_playing_and_plays_when_paused(media: TabMedia) -> None:
    actions: list[str] = []
    media.actionRequested.connect(lambda action, _seconds: actions.append(action))

    media.apply(PLAYING)
    media.togglePlayback()
    media.apply(PAUSED)
    media.togglePlayback()

    assert actions == ["pause", "play"]


def test_clear_is_a_slot_callable_from_qml(media: TabMedia) -> None:
    meta = media.metaObject()
    signatures = [meta.method(i).methodSignature().data() for i in range(meta.methodCount())]

    assert b"clear()" in signatures


def test_clear_resets_media_state(media: TabMedia) -> None:
    media.apply(PLAYING)

    media.clear()

    assert not media.hasMedia
