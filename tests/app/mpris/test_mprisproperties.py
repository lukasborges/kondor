from dataclasses import replace

from PySide6.QtCore import QUrl

from kondor.app.mpris.mprisproperties import PlayerSnapshot, player_properties, root_properties
from kondor.browser.media.mediastate import MediaState
from tests.browser.media.mediafakes import PAUSED, PLAYING


def snapshot(state: MediaState = PLAYING, **changes: object) -> PlayerSnapshot:
    base = PlayerSnapshot(state, 12.5, 3, "https://site.example/watch", False, "Kondor Browser")
    return replace(base, **changes)  # type: ignore[arg-type]


def test_root_values() -> None:
    values = root_properties("Kondor Browser", "kondor")

    assert values["CanRaise"] == ("b", True)
    assert values["CanQuit"] == ("b", False)
    assert values["Identity"] == ("s", "Kondor Browser")
    assert values["DesktopEntry"] == ("s", "kondor")
    assert values["SupportedUriSchemes"] == ("as", [])


def test_playback_status_follows_playing() -> None:
    assert player_properties(snapshot())["PlaybackStatus"] == ("s", "Playing")
    assert player_properties(snapshot(PAUSED))["PlaybackStatus"] == ("s", "Paused")


def test_position_is_in_microseconds() -> None:
    assert player_properties(snapshot())["Position"] == ("x", 12_500_000)


def test_capabilities_follow_the_page_actions() -> None:
    values = player_properties(snapshot())
    bare = player_properties(snapshot(replace(PLAYING, actions=frozenset(), duration=0.0)))

    assert (values["CanGoNext"], values["CanGoPrevious"], values["CanSeek"]) == (
        ("b", True),
        ("b", True),
        ("b", True),
    )
    assert (bare["CanGoNext"], bare["CanGoPrevious"], bare["CanSeek"]) == (
        ("b", False),
        ("b", False),
        ("b", False),
    )


def test_metadata_describes_the_track() -> None:
    _, metadata = player_properties(snapshot())["Metadata"]

    assert metadata["mpris:trackid"] == ("o", "/io/github/lukasborges/Kondor/track/3")
    assert metadata["mpris:length"] == ("x", 200_000_000)
    assert metadata["xesam:title"] == ("s", "Song")
    assert metadata["xesam:artist"] == ("as", ["Band"])
    assert metadata["xesam:album"] == ("s", "Record")
    assert metadata["mpris:artUrl"] == ("s", "https://example.com/cover.png")
    assert metadata["xesam:url"] == ("s", "https://site.example/watch")


def test_length_and_empty_fields_are_omitted() -> None:
    state = replace(PLAYING, duration=0.0, album="", artwork_url=QUrl())

    _, metadata = player_properties(snapshot(state))["Metadata"]

    assert {"mpris:length", "xesam:album", "mpris:artUrl"} & set(metadata) == set()


def test_track_id_changes_with_the_track_number() -> None:
    first = player_properties(snapshot())["Metadata"][1]["mpris:trackid"]
    second = player_properties(snapshot(track_number=4))["Metadata"][1]["mpris:trackid"]

    assert first != second


def test_private_tab_metadata_has_only_the_app_name() -> None:
    _, metadata = player_properties(snapshot(is_private=True))["Metadata"]

    assert set(metadata) == {"mpris:trackid", "mpris:length", "xesam:title"}
    assert metadata["xesam:title"] == ("s", "Kondor Browser")
