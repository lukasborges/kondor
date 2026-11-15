from typing import Any

import pytest
from PySide6.QtGui import QKeySequence

from kondor.extensions.action.actionitemdisplay import for_display

PLAIN_ICON_SOURCES = ("/tmp/x.png", "file:///tmp/x.png", "https://example.com/x.png")


def displayed_item(item: dict[str, Any], values: dict[str, Any] | None = None) -> dict[str, Any]:
    return for_display([item], values or {})[0]


def keyed_item() -> dict[str, Any]:
    return {"keysSetting": "keyFaster"}


def values_of(keys: str) -> dict[str, Any]:
    return {"keyFaster": keys}


def test_shortcut_shows_current_keys_value(qapp: object) -> None:
    expected = QKeySequence("Ctrl+S").toString(QKeySequence.SequenceFormat.NativeText)
    assert displayed_item(keyed_item(), values_of("Ctrl+S"))["shortcut"] == expected


def test_item_without_keys_setting_has_no_shortcut(qapp: object) -> None:
    assert displayed_item({}, values_of("S"))["shortcut"] == ""


@pytest.mark.parametrize("keys", ["Ctrl+NoSuchKey", ""])
def test_unparsable_keys_value_has_no_shortcut(qapp: object, keys: str) -> None:
    assert displayed_item(keyed_item(), values_of(keys))["shortcut"] == ""


def test_missing_theme_icon_is_dropped(qapp: object) -> None:
    assert displayed_item({"icon": "no-such-icon-anywhere"})["icon"] == ""


@pytest.mark.parametrize("source", PLAIN_ICON_SOURCES)
def test_icon_path_or_url_is_dropped(qapp: object, source: str) -> None:
    assert displayed_item({"icon": source})["icon"] == ""
