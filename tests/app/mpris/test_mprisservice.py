from dataclasses import replace

import pytest
from pytestqt.qtbot import QtBot

from kondor.app.mpris.mprisservice import MprisService, bus_name_for
from kondor.app.windows.windowmanager import WindowManager
from kondor.browser.tabs.tab import Tab
from kondor.core.dbus.buscall import BusCall, BusError, BusReply
from tests.app.mpris.servicefakes import PLAYER, PROPERTIES, ROOT, Calls, FakeBus
from tests.browser.media.mediafakes import PAUSED, PLAYING

SEEKED_MICROSECONDS = 7_000_000


def test_bus_name_is_built_from_the_unique_name() -> None:
    assert bus_name_for(":1.234") == "org.mpris.MediaPlayer2.kondor.instance_1_234"


def test_bus_starts_when_a_tab_becomes_current(bus: FakeBus, tab: Tab) -> None:
    assert bus.is_running
    assert bus.names == ["org.mpris.MediaPlayer2.kondor.instance_1_234"]


def test_bus_stops_when_no_tab_is_left(bus: FakeBus, tab: Tab) -> None:
    tab.media.clear()

    assert not bus.is_running


def test_get_returns_a_variant(calls: Calls) -> None:
    reply = calls.to(PROPERTIES, "Get", PLAYER, "PlaybackStatus")

    assert reply == BusReply("v", (("s", "Playing"),))


def test_get_all_returns_the_interface(calls: Calls) -> None:
    reply = calls.to(PROPERTIES, "GetAll", ROOT)

    assert isinstance(reply, BusReply) and reply.signature == "a{sv}"
    assert reply.body[0]["CanRaise"] == ("b", True)


def test_get_unknown_property_is_an_error(calls: Calls) -> None:
    reply = calls.to(PROPERTIES, "Get", PLAYER, "Nothing")

    assert reply == BusError("org.freedesktop.DBus.Error.UnknownProperty")


def test_set_is_read_only(calls: Calls) -> None:
    reply = calls.to(PROPERTIES, "Set", PLAYER, "Volume", ("d", 0.5))

    assert reply == BusError("org.freedesktop.DBus.Error.PropertyReadOnly")


def test_other_paths_are_not_answered(service: MprisService, tab: Tab) -> None:
    assert service.handle_call(BusCall("/other", PLAYER, "Play", ())) is None


def test_introspect_returns_xml(calls: Calls, staged_resources: None) -> None:
    reply = calls.to("org.freedesktop.DBus.Introspectable", "Introspect")

    assert isinstance(reply, BusReply) and PLAYER in reply.body[0]


def test_raise_shows_the_tab(calls: Calls, tab: Tab, monkeypatch: pytest.MonkeyPatch) -> None:
    shown: list[object] = []
    monkeypatch.setattr(WindowManager, "show_tab", lambda self, t, token=b"": shown.append(t))

    assert calls.to(ROOT, "Raise") == BusReply()
    assert shown == [tab]


def test_quit_does_nothing(calls: Calls) -> None:
    assert calls.to(ROOT, "Quit") == BusReply()


def test_properties_changed_carries_only_changed_values(
    bus: FakeBus, tab: Tab, qtbot: QtBot
) -> None:
    qtbot.wait(20)
    bus.signals.clear()

    tab.media.apply(replace(PAUSED, position=99.0))
    qtbot.waitUntil(lambda: bool(bus.signals))

    (signal,) = bus.signals
    assert signal.member == "PropertiesChanged"
    assert signal.body[1] == {"PlaybackStatus": ("s", "Paused")}


def test_seeked_is_emitted(bus: FakeBus, tab: Tab, qtbot: QtBot) -> None:
    qtbot.wait(20)

    tab.media.apply(replace(PLAYING, position=7.0, was_seeked=True))

    seeked = [s for s in bus.signals if s.member == "Seeked"]
    assert seeked and seeked[0].body[0] >= SEEKED_MICROSECONDS


def test_title_change_starts_a_new_track(service: MprisService, tab: Tab) -> None:
    before = service.player_values()["Metadata"][1]["mpris:trackid"]

    tab.setTitle("Another page")

    assert service.player_values()["Metadata"][1]["mpris:trackid"] != before
