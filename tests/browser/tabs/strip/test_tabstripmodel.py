from collections.abc import Iterator

import pytest
from PySide6.QtCore import QModelIndex, Qt

from kondor.browser.tabs.strip.striprow import LABEL, TAB, StripRole
from kondor.browser.tabs.strip.tabstripmodel import TabStripModel
from kondor.browser.tabs.tabmodel import TabModel
from tests.browser.tabs.strip.signals import Signals

pytestmark = pytest.mark.no_qt_log

FOUR_TABS = 4
SECOND_TAB = 2


@pytest.fixture
def strip(model: TabModel) -> Iterator[TabStripModel]:
    strip_model = TabStripModel()
    strip_model.setProperty("source", model)
    yield strip_model
    strip_model.deleteLater()


def kinds(strip: TabStripModel) -> list[str]:
    return [strip.data(strip.index(row, 0), StripRole.KIND) for row in range(strip.rowCount())]


def hidden(strip: TabStripModel) -> list[bool]:
    return [strip.data(strip.index(row, 0), StripRole.IS_HIDDEN) for row in range(strip.rowCount())]


def add_tabs(model: TabModel, count: int) -> list:
    return [model.addTab() for _ in range(count)]


def grouped_pair(model: TabModel):
    tabs = add_tabs(model, FOUR_TABS)
    group = model.newGroupForTab(1)
    model.addTabToGroup(2, group)
    return tabs, group


def test_ungrouped_tabs_have_no_label_rows(model: TabModel, strip: TabStripModel) -> None:
    add_tabs(model, 3)
    assert kinds(strip) == [TAB] * 3


def test_label_row_comes_right_before_the_first_tab_of_its_group(
    model: TabModel, strip: TabStripModel
) -> None:
    grouped_pair(model)
    assert kinds(strip) == [TAB, LABEL, TAB, TAB, TAB]


def test_pinned_tabs_are_flagged(model: TabModel, strip: TabStripModel) -> None:
    add_tabs(model, 2)
    model.setPinned(1, True)
    assert strip.data(strip.index(0, 0), StripRole.IS_PINNED) is True
    assert strip.data(strip.index(1, 0), StripRole.IS_PINNED) is False


def test_collapsing_hides_the_tabs_and_keeps_the_label(
    model: TabModel, strip: TabStripModel
) -> None:
    _, group = grouped_pair(model)
    model.setCurrentIndex(0)
    signals = Signals(strip)
    model.setGroupCollapsed(group, True)
    assert hidden(strip) == [False, False, True, True, False]
    assert signals.structure_is_untouched()
    assert {row for first, last in signals.changed for row in range(first, last + 1)} >= {2, 3}
    assert min(first for first, _ in signals.changed) >= 1


def test_closing_the_first_tab_of_the_strip_moves_nothing_else(
    model: TabModel, strip: TabStripModel
) -> None:
    grouped_pair(model)
    signals = Signals(strip)
    model.closeTab(0)
    assert kinds(strip) == [LABEL, TAB, TAB, TAB]
    assert signals.removed == [(0, 0)]
    assert not (signals.inserted or signals.moved or signals.resets)


def test_closing_the_first_tab_of_a_group_keeps_the_label_first(
    model: TabModel, strip: TabStripModel
) -> None:
    tabs, _ = grouped_pair(model)
    model.closeTab(1)
    assert kinds(strip) == [TAB, LABEL, TAB, TAB]
    assert strip.data(strip.index(2, 0), StripRole.TAB) is tabs[2]


def test_removing_the_last_tab_of_a_group_removes_its_label(
    model: TabModel, strip: TabStripModel
) -> None:
    grouped_pair(model)
    signals = Signals(strip)
    model.closeGroup(model.groupAt(1))
    assert kinds(strip) == [TAB, TAB]
    assert signals.resets == 0
    assert (1, 1) in signals.removed


def test_moving_a_tab_inside_a_group_keeps_the_label_in_place(
    model: TabModel, strip: TabStripModel
) -> None:
    tabs, _ = grouped_pair(model)
    signals = Signals(strip)
    model.moveTab(2, 1)
    assert kinds(strip) == [TAB, LABEL, TAB, TAB, TAB]
    assert len(signals.moved) == 1
    assert 1 not in signals.moved[0][:2]
    assert not (signals.inserted or signals.removed or signals.resets)
    assert strip.data(strip.index(2, 0), StripRole.TAB) is tabs[2]


def test_moving_a_group_moves_its_label_with_it(model: TabModel, strip: TabStripModel) -> None:
    _, group = grouped_pair(model)
    model.moveGroup(group, FOUR_TABS)
    assert kinds(strip) == [TAB, TAB, LABEL, TAB, TAB]


def test_moving_a_group_emits_row_moves_instead_of_a_reset(
    model: TabModel, strip: TabStripModel
) -> None:
    _, group = grouped_pair(model)
    signals = Signals(strip)
    model.moveGroup(group, FOUR_TABS)
    assert signals.moved
    assert signals.resets == 0


def test_renaming_a_group_changes_its_label_row_only(model: TabModel, strip: TabStripModel) -> None:
    _, group = grouped_pair(model)
    signals = Signals(strip)
    group.setName("Work")
    assert strip.rowCount() == FOUR_TABS + 1
    assert signals.structure_is_untouched()
    assert signals.changed == []


def test_adding_a_group_inserts_one_label_row(model: TabModel, strip: TabStripModel) -> None:
    add_tabs(model, 2)
    inserted: list[int] = []
    strip.rowsInserted.connect(lambda _parent, first, _last: inserted.append(first))
    model.newGroupForTab(1)
    assert inserted == [1]


def test_ungrouping_removes_the_label_row(model: TabModel, strip: TabStripModel) -> None:
    _, group = grouped_pair(model)
    model.ungroup(group)
    assert kinds(strip) == [TAB] * FOUR_TABS


def test_row_of_a_tab_skips_the_label_rows(model: TabModel, strip: TabStripModel) -> None:
    tabs, _ = grouped_pair(model)
    assert [strip.rowOfTab(tab) for tab in tabs] == [0, 2, 3, 4]
    assert strip.rowOfTabIndex(1) == SECOND_TAB


def test_tab_index_of_a_label_is_the_first_tab_of_its_group(
    model: TabModel, strip: TabStripModel
) -> None:
    grouped_pair(model)
    assert strip.tabIndexAt(1) == 1
    assert strip.tabIndexAt(2) == 1
    assert strip.tabIndexAt(3) == SECOND_TAB


def test_role_names_expose_the_strip_roles(strip: TabStripModel) -> None:
    names = {bytes(name).decode() for name in strip.roleNames().values()}
    assert names == {"kind", "tab", "group", "isHidden", "isPinned", "tabIndex"}


def test_an_unknown_index_has_no_data(strip: TabStripModel) -> None:
    assert strip.data(QModelIndex(), Qt.ItemDataRole.DisplayRole) is None
