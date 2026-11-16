from dataclasses import dataclass
from typing import Any

from kondor.browser.media.mediastate import MediaState

PLAYER_INTERFACE = "org.mpris.MediaPlayer2.Player"
ROOT_INTERFACE = "org.mpris.MediaPlayer2"
TRACK_PATH_PREFIX = "/io/github/lukasborges/Kondor/track/"
MICROSECONDS = 1_000_000

Variant = tuple[str, Any]
Properties = dict[str, Variant]


@dataclass(frozen=True)
class PlayerSnapshot:
    state: MediaState
    position: float
    track_number: int
    url: str
    is_private: bool
    identity: str

    @property
    def track_id(self) -> str:
        return f"{TRACK_PATH_PREFIX}{self.track_number}"


def microseconds(seconds: float) -> int:
    return int(seconds * MICROSECONDS)


def root_properties(identity: str, desktop_entry: str) -> Properties:
    return {
        "CanQuit": ("b", False),
        "CanRaise": ("b", True),
        "HasTrackList": ("b", False),
        "Identity": ("s", identity),
        "DesktopEntry": ("s", desktop_entry),
        "SupportedUriSchemes": ("as", []),
        "SupportedMimeTypes": ("as", []),
    }


def optional_text(key: str, value: str) -> Properties:
    return {key: ("s", value)} if value else {}


def public_metadata(snapshot: PlayerSnapshot) -> Properties:
    state = snapshot.state
    return {
        "xesam:title": ("s", state.title),
        "xesam:artist": ("as", [state.artist]),
        "xesam:url": ("s", snapshot.url),
        **optional_text("xesam:album", state.album),
        **optional_text("mpris:artUrl", state.artwork_url.toString()),
    }


def metadata_of(snapshot: PlayerSnapshot) -> Properties:
    state = snapshot.state
    metadata: Properties = {"mpris:trackid": ("o", snapshot.track_id)}
    if state.duration > 0:
        metadata["mpris:length"] = ("x", microseconds(state.duration))
    if snapshot.is_private:
        metadata["xesam:title"] = ("s", snapshot.identity)
        return metadata
    return {**metadata, **public_metadata(snapshot)}


def playback_properties(snapshot: PlayerSnapshot) -> Properties:
    state = snapshot.state
    return {
        "PlaybackStatus": ("s", "Playing" if state.is_playing else "Paused"),
        "Rate": ("d", state.rate),
        "MinimumRate": ("d", min(1.0, state.rate)),
        "MaximumRate": ("d", max(1.0, state.rate)),
        "Volume": ("d", 1.0),
        "Metadata": ("a{sv}", metadata_of(snapshot)),
        "Position": ("x", microseconds(snapshot.position)),
    }


def capability_properties(state: MediaState) -> Properties:
    return {
        "CanGoNext": ("b", "nexttrack" in state.actions),
        "CanGoPrevious": ("b", "previoustrack" in state.actions),
        "CanPlay": ("b", True),
        "CanPause": ("b", True),
        "CanControl": ("b", True),
        "CanSeek": ("b", state.duration > 0),
    }


def player_properties(snapshot: PlayerSnapshot) -> Properties:
    return {**playback_properties(snapshot), **capability_properties(snapshot.state)}
