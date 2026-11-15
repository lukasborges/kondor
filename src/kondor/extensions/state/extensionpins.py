from typing import Any

from kondor.core.settings.settings import Settings


def changed_pins(pins: list[str], extension_id: str, is_pinned: bool) -> list[str]:
    if is_pinned:
        return pins if extension_id in pins else [*pins, extension_id]
    return [pin for pin in pins if pin != extension_id]


def entry_with_id(entries: list[Any], extension_id: str) -> Any:
    return next((entry for entry in entries if entry.get("id") == extension_id), None)


def is_pinned(extension_id: str) -> bool:
    return extension_id in Settings.instance().pinnedExtensions


def set_pinned(extension_id: str, pinned: bool) -> None:
    settings = Settings.instance()
    settings.pinnedExtensions = changed_pins(settings.pinnedExtensions, extension_id, pinned)


def only_pinned(entries: list[Any]) -> list[Any]:
    found = (entry_with_id(entries, pin) for pin in Settings.instance().pinnedExtensions)
    return [entry for entry in found if entry is not None]
