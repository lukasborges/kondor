from dataclasses import replace

import pytest

from kondor.app.mpris.mprisservice import MprisService
from kondor.browser.tabs.tab import Tab
from kondor.core.dbus.buscall import BusError, BusReply
from tests.app.mpris.servicefakes import Calls
from tests.browser.media.mediafakes import PLAYING

SEEK_TARGET = 15.0
SEEK_FORWARD_MICROSECONDS = 5_000_000
STALE_TRACK = "/io/github/lukasborges/Kondor/track/999"


@pytest.mark.parametrize(
    ("method", "action"),
    [
        ("Play", "play"),
        ("Pause", "pause"),
        ("PlayPause", "pause"),
        ("Stop", "stop"),
        ("Next", "nexttrack"),
        ("Previous", "previoustrack"),
    ],
)
def test_methods_map_to_tab_commands(calls: Calls, method: str, action: str) -> None:
    reply = calls.player(method)

    assert reply == BusReply()
    assert calls.actions == [(action, 0.0)]


def test_next_does_nothing_without_a_page_handler(calls: Calls, tab: Tab) -> None:
    tab.media.apply(replace(PLAYING, actions=frozenset()))

    calls.player("Next")

    assert calls.actions == []


def test_seek_moves_relative_to_the_position(calls: Calls) -> None:
    calls.player("Seek", SEEK_FORWARD_MICROSECONDS)

    assert calls.actions[0][0] == "seekto" and calls.actions[0][1] >= SEEK_TARGET


def test_seek_past_the_end_goes_to_the_next_track(calls: Calls) -> None:
    calls.player("Seek", 999_000_000)

    assert calls.actions == [("nexttrack", 0.0)]


def test_set_position_with_a_stale_track_id_is_ignored(calls: Calls) -> None:
    calls.player("SetPosition", STALE_TRACK, 1_000_000)

    assert calls.actions == []


def test_set_position_with_the_current_track_id_seeks(calls: Calls, service: MprisService) -> None:
    track_id = service.player_values()["Metadata"][1]["mpris:trackid"][1]

    calls.player("SetPosition", track_id, 30_000_000)

    assert calls.actions == [("seekto", 30.0)]


def test_open_uri_is_not_supported(calls: Calls) -> None:
    assert calls.player("OpenUri", "file:///a") == BusError(
        "org.freedesktop.DBus.Error.NotSupported"
    )
