from typing import Any

from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QIcon, QKeySequence

PLAIN_NAME = QRegularExpression(r"^[A-Za-z0-9_.-]+$")


def string_of(value: Any) -> str:
    return str(value) if isinstance(value, str) else ""


def theme_icon_or_empty(name: str) -> str:
    is_plain = PLAIN_NAME.match(name).hasMatch()
    return name if is_plain and QIcon.hasThemeIcon(name) else ""


def is_parsed(sequence: QKeySequence) -> bool:
    return not sequence.isEmpty() and sequence[0].toCombined() != Qt.Key.Key_unknown.value


def native_shortcut(portable_text: str) -> str:
    sequence = QKeySequence.fromString(portable_text, QKeySequence.SequenceFormat.PortableText)
    if not is_parsed(sequence):
        return ""
    return str(sequence.toString(QKeySequence.SequenceFormat.NativeText))


def shortcut_of(item: dict[str, Any], setting_values: dict[str, Any]) -> str:
    keys_setting = string_of(item.get("keysSetting"))
    if not keys_setting:
        return ""
    return native_shortcut(string_of(setting_values.get(keys_setting)))


def displayed(item: dict[str, Any], setting_values: dict[str, Any]) -> dict[str, Any]:
    icon = theme_icon_or_empty(string_of(item.get("icon")))
    return {**item, "icon": icon, "shortcut": shortcut_of(item, setting_values)}


def for_display(items: list[Any], setting_values: dict[str, Any]) -> list[dict[str, Any]]:
    return [displayed(item, setting_values) for item in items]
