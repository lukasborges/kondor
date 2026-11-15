import pytest
from PySide6.QtCore import QObject, Signal

from kondor.browser.tabs.assignandnotify import assign_and_notify


class Holder(QObject):
    changed = Signal()

    def __init__(self, value: object) -> None:
        super().__init__()
        self.value = value
        self.notifications = 0
        self.changed.connect(self._count)

    def _count(self) -> None:
        self.notifications += 1


def test_equal_value_does_not_notify(qapp: object) -> None:
    holder = Holder("same")
    assign_and_notify((holder, "value"), "same", holder.changed)
    assert holder.notifications == 0


def test_new_value_is_stored_and_notified(qapp: object) -> None:
    holder = Holder("old")
    assign_and_notify((holder, "value"), "new", holder.changed)
    assert (holder.value, holder.notifications) == ("new", 1)


@pytest.mark.parametrize(
    ("first", "second", "is_same"),
    [(0.0, 0.0, True), (0.0, 1e-13, False), (1.0, 1.0 + 1e-13, True)],
)
def test_floats_use_the_fuzzy_rule(first: float, second: float, is_same: bool) -> None:
    holder = Holder(first)
    assign_and_notify((holder, "value"), second, holder.changed)
    assert (holder.notifications == 0) is is_same
