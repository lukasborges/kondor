from collections.abc import Callable
from typing import Any

from kondor.browser.tabs.features.tabmedia import TabMedia
from kondor.core.dbus.buscall import BusCall, BusError, BusReply

NOT_SUPPORTED = "org.freedesktop.DBus.Error.NotSupported"
MICROSECONDS = 1_000_000
EMPTY_REPLY = BusReply()


def go_next(media: TabMedia) -> None:
    if "nexttrack" in media.state.actions:
        media.next()


def go_previous(media: TabMedia) -> None:
    if "previoustrack" in media.state.actions:
        media.previous()


def seek_by(media: TabMedia, offset: int) -> None:
    target = max(0.0, media.current_position() + offset / MICROSECONDS)
    duration = media.state.duration
    if duration > 0 and target > duration:
        go_next(media)
        return
    media.seekTo(target)


def set_position(media: TabMedia, current_track_id: str, body: tuple[Any, ...]) -> None:
    track_id, position = body
    length = media.state.duration * MICROSECONDS
    if track_id == current_track_id and 0 <= position <= length:
        media.seekTo(position / MICROSECONDS)


def simple_methods() -> dict[str, Callable[[TabMedia], None]]:
    return {
        "Play": TabMedia.play,
        "Pause": TabMedia.pause,
        "PlayPause": TabMedia.togglePlayback,
        "Stop": TabMedia.stop,
        "Next": go_next,
        "Previous": go_previous,
    }


def run_method(media: TabMedia, current_track_id: str, call: BusCall) -> None:
    simple = simple_methods().get(call.member)
    if simple is not None:
        simple(media)
    elif call.member == "Seek":
        seek_by(media, *call.body)
    elif call.member == "SetPosition":
        set_position(media, current_track_id, call.body)


def player_call(
    media: TabMedia | None, current_track_id: str, call: BusCall
) -> BusReply | BusError | None:
    if call.member == "OpenUri":
        return BusError(NOT_SUPPORTED)
    if call.member not in {*simple_methods(), "Seek", "SetPosition"}:
        return None
    if media is not None:
        run_method(media, current_track_id, call)
    return EMPTY_REPLY
