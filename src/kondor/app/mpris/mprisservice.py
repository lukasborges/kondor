from collections.abc import Callable
from typing import ClassVar

import shiboken6
from PySide6.QtCore import QFile, QIODevice, QObject
from PySide6.QtGui import QGuiApplication

from kondor.app.mpris.mprisplayercalls import player_call
from kondor.app.mpris.mprisproperties import (
    PLAYER_INTERFACE,
    ROOT_INTERFACE,
    Properties,
    player_properties,
    root_properties,
)
from kondor.app.mpris.mprispropertycalls import PROPERTIES_INTERFACE, property_call
from kondor.app.mpris.mprisrelay import MediaRelay
from kondor.app.mpris.mprissignals import OBJECT_PATH, PlayerSignals
from kondor.app.mpris.mprissnapshot import snapshot_of, tab_of
from kondor.app.startup.appidentity import desktop_file_name
from kondor.app.windows.windowmanager import WindowManager
from kondor.browser.media.mediatabs import MediaTabs
from kondor.browser.tabs.features.tabmedia import TabMedia
from kondor.core.dbus.buscall import BusCall, BusError, BusReply
from kondor.core.dbus.sessionbusservice import SessionBusService

NAME_PREFIX = "org.mpris.MediaPlayer2.kondor.instance_"
INTROSPECTABLE_INTERFACE = "org.freedesktop.DBus.Introspectable"
INTROSPECTION_RESOURCE = ":/mpris/mprisintrospection.xml"
Handler = Callable[[BusCall], BusReply | BusError | None]


def bus_name_for(unique_name: str) -> str:
    return NAME_PREFIX + unique_name.lstrip(":").replace(".", "_")


def introspection_xml() -> str:
    file = QFile(INTROSPECTION_RESOURCE)
    if not file.open(QIODevice.OpenModeFlag.ReadOnly):
        return ""
    return bytes(file.readAll().data()).decode()


class MprisService(QObject):
    _instance: ClassVar["MprisService | None"] = None

    def __init__(self) -> None:
        super().__init__()
        self._bus = SessionBusService(self.handle_call, self)
        self._signals = PlayerSignals(self._bus, self.player_values, self)
        self._watched: TabMedia | None = None
        self._relay: MediaRelay | None = None
        self._track_number = 0

    @classmethod
    def instance(cls) -> "MprisService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start(self) -> None:
        MediaTabs.instance().currentChanged.connect(self.follow_current)
        self.follow_current()

    def stop(self) -> None:
        MediaTabs.instance().currentChanged.disconnect(self.follow_current)
        self.unwatch()
        self._bus.stop()

    def follow_current(self) -> None:
        media = MediaTabs.instance().current
        self.unwatch()
        if media is None:
            self._bus.stop()
            return
        self.watch(media)
        if not self._bus.is_running and self._bus.start(bus_name_for):
            self._signals.remember_current_values()
        self._signals.schedule_flush()

    def watch(self, media: TabMedia) -> None:
        self._watched = media
        self._track_number += 1
        self._relay = MediaRelay(media)
        self._relay.changed.connect(self._signals.schedule_flush)
        self._relay.titleChanged.connect(self.start_new_track)
        self._relay.seeked.connect(self.send_seeked)

    def unwatch(self) -> None:
        self._watched = None
        if self._relay is not None:
            shiboken6.delete(self._relay)
            self._relay = None

    def start_new_track(self) -> None:
        self._track_number += 1
        self._signals.schedule_flush()

    def send_seeked(self) -> None:
        if self._watched is not None:
            self._signals.send_seeked(self._watched.current_position())

    def player_values(self) -> Properties:
        return player_properties(snapshot_of(self._watched, self._track_number))

    def interfaces(self) -> dict[str, Properties]:
        identity = QGuiApplication.applicationDisplayName()
        return {
            ROOT_INTERFACE: root_properties(identity, desktop_file_name()),
            PLAYER_INTERFACE: self.player_values(),
        }

    def handlers(self) -> dict[str, Handler]:
        return {
            PROPERTIES_INTERFACE: lambda call: property_call(self.interfaces(), call),
            INTROSPECTABLE_INTERFACE: self.introspect_call,
            ROOT_INTERFACE: self.root_call,
            PLAYER_INTERFACE: self.player_method_call,
        }

    def handle_call(self, call: BusCall) -> BusReply | BusError | None:
        handler = self.handlers().get(call.interface)
        return handler(call) if handler is not None and call.path == OBJECT_PATH else None

    @staticmethod
    def introspect_call(call: BusCall) -> BusReply | None:
        return BusReply("s", (introspection_xml(),)) if call.member == "Introspect" else None

    def player_method_call(self, call: BusCall) -> BusReply | BusError | None:
        track_id = snapshot_of(self._watched, self._track_number).track_id
        return player_call(self._watched, track_id, call)

    def root_call(self, call: BusCall) -> BusReply | None:
        if call.member == "Raise":
            self.raise_tab()
        return BusReply() if call.member in ("Raise", "Quit") else None

    def raise_tab(self) -> None:
        tab = tab_of(self._watched)
        if tab is not None:
            WindowManager.instance().show_tab(tab)
