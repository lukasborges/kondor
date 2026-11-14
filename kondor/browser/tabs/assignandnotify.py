from typing import Any

from PySide6.QtCore import SignalInstance

FUZZY_FACTOR = 1e12


def is_same(first: object, second: object) -> bool:
    if isinstance(first, float) and isinstance(second, float):
        return abs(first - second) * FUZZY_FACTOR <= min(abs(first), abs(second))
    return bool(first == second)


def assign_and_notify(member: tuple[object, str], value: Any, signal: SignalInstance) -> None:
    owner, attribute = member
    if is_same(getattr(owner, attribute), value):
        return
    setattr(owner, attribute, value)
    signal.emit()
