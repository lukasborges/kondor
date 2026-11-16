from typing import Any

import pytest

from kondor.app.mpris.mprisservice import MprisService
from kondor.browser.tabs.tab import Tab
from kondor.core.dbus.buscall import BusCall, BusError, BusReply, BusSignal
from tests.browser.media.mediafakes import PLAYING

PATH = "/org/mpris/MediaPlayer2"
PLAYER = "org.mpris.MediaPlayer2.Player"
ROOT = "org.mpris.MediaPlayer2"
PROPERTIES = "org.freedesktop.DBus.Properties"
Reply = BusReply | BusError | None


class FakeBus:
    def __init__(self) -> None:
        self.is_running = False
        self.names: list[str] = []
        self.signals: list[BusSignal] = []

    def start(self, name: Any) -> bool:
        self.names.append(name(":1.234"))
        self.is_running = True
        return True

    def stop(self) -> None:
        self.is_running = False

    def emit_signal(self, signal: BusSignal) -> None:
        self.signals.append(signal)


class Calls:
    def __init__(self, service: MprisService, tab: Tab) -> None:
        self.service = service
        self.actions: list[tuple[str, float]] = []
        tab.media.actionRequested.connect(lambda a, s: self.actions.append((a, s)))

    def to(self, interface: str, member: str, *body: Any) -> Reply:
        return self.service.handle_call(BusCall(PATH, interface, member, body))

    def player(self, member: str, *body: Any) -> Reply:
        return self.to(PLAYER, member, *body)


@pytest.fixture
def service(fresh_media_tabs: object) -> MprisService:
    mpris = MprisService()
    mpris._bus = FakeBus()  # type: ignore[assignment]
    mpris._signals._bus = mpris._bus  # type: ignore[assignment]
    mpris.start()
    return mpris


@pytest.fixture
def bus(service: MprisService) -> FakeBus:
    return service._bus  # type: ignore[return-value]


@pytest.fixture
def tab(service: MprisService) -> Tab:
    media_tab = Tab(None)
    media_tab.media.apply(PLAYING)
    return media_tab


@pytest.fixture
def calls(service: MprisService, tab: Tab) -> Calls:
    return Calls(service, tab)
