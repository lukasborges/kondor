from PySide6.QtCore import QUrl

from kondor.browser.media.mediastate import MAX_TEXT_LENGTH, MediaState, parse_report


def test_report_without_media_is_the_empty_state() -> None:
    assert parse_report({"hasMedia": False}) == MediaState()


def test_report_with_wrong_types_gets_defaults() -> None:
    report = {"hasMedia": True, "title": 5, "duration": "long", "rate": None, "actions": "play"}

    state = parse_report(report)

    assert (state.title, state.duration, state.rate, state.actions) == ("", 0.0, 1.0, frozenset())


def test_text_is_trimmed_and_cut() -> None:
    state = parse_report({"hasMedia": True, "title": "  " + "x" * 600 + "  "})

    assert state.title == "x" * MAX_TEXT_LENGTH


def test_negative_and_infinite_numbers_become_defaults() -> None:
    report = {"hasMedia": True, "duration": float("inf"), "position": -3, "rate": -1}

    state = parse_report(report)

    assert (state.duration, state.position, state.rate) == (0.0, 0.0, 1.0)


def test_only_web_artwork_is_kept() -> None:
    web = parse_report({"hasMedia": True, "artworkUrl": "https://a.example/c.png"})
    local = parse_report({"hasMedia": True, "artworkUrl": "file:///etc/passwd"})

    assert web.artwork_url == QUrl("https://a.example/c.png")
    assert local.artwork_url == QUrl()


def test_unknown_actions_are_dropped() -> None:
    report = {"hasMedia": True, "actions": ["play", "nexttrack", "hangup", 3]}

    assert parse_report(report).actions == frozenset({"play", "nexttrack"})


def test_playing_and_seeked_flags_are_read() -> None:
    state = parse_report({"hasMedia": True, "playing": True, "seeked": True, "position": 4.5})

    assert (state.is_playing, state.was_seeked, state.position) == (True, True, 4.5)
