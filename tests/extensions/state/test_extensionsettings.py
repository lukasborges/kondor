from typing import Any

import pytest

from kondor.extensions.state.extensionsettings import sanitize_setting

FALLBACK = "fallback"


def setting_of(setting_type: str) -> dict[str, Any]:
    return {"type": setting_type, "default": FALLBACK}


def bool_setting(default: bool) -> dict[str, Any]:
    return {"type": "bool", "default": default}


def choice_setting() -> dict[str, Any]:
    return {**setting_of("choice"), "choices": [{"value": "a"}]}


ROWS = {
    "bool good": (bool_setting(False), True, True),
    "bool true text": (bool_setting(False), "true", True),
    "bool false text": (bool_setting(True), "false", False),
    "bool bad": (bool_setting(False), "yes", False),
    "number good": (setting_of("number"), 5, 5.0),
    "number numeric text": (setting_of("number"), "7", 7.0),
    "number bad": (setting_of("number"), "x", FALLBACK),
    "choice good": (choice_setting(), "a", "a"),
    "choice bad": (choice_setting(), "z", FALLBACK),
    "string good": (setting_of("string"), "value", "value"),
    "string bad": (setting_of("text"), 3, FALLBACK),
    "color bad": (setting_of("color"), True, FALLBACK),
    "keys good": (setting_of("keys"), "k", "k"),
}

CLAMP_ROWS = {"above": (500.0, 100.0), "below": (-5.0, 0.0), "inside": (42.0, 42.0)}


@pytest.mark.parametrize(("setting", "value", "expected"), ROWS.values(), ids=ROWS)
def test_sanitizes_each_setting_type(setting: dict[str, Any], value: Any, expected: Any) -> None:
    assert sanitize_setting(setting, value) == expected


@pytest.mark.parametrize(("value", "expected"), CLAMP_ROWS.values(), ids=CLAMP_ROWS)
def test_clamps_numbers_to_min_and_max(value: float, expected: float) -> None:
    setting = {**setting_of("number"), "min": 0, "max": 100}
    assert sanitize_setting(setting, value) == expected
