import pytest

from kondor.browser.tabs.tabmodel import TabModel

pytestmark = pytest.mark.no_qt_log

LAST_OF_THREE = 2


def add_tabs(model: TabModel, count: int) -> list:
    return [model.addTab() for _ in range(count)]


def grouped_pair_in_middle(model: TabModel) -> tuple[list, object]:
    tabs = add_tabs(model, 4)
    group = model.newGroupForTab(1)
    model.addTabToGroup(2, group)
    return tabs, group


def test_moving_a_grouped_tab_before_its_group_clamps_to_the_first_row(model: TabModel) -> None:
    tabs, group = grouped_pair_in_middle(model)
    model.moveTab(2, 0)
    assert [model.indexOfTab(tab) for tab in tabs] == [0, 2, 1, 3]
    assert tabs[2].group is group


def test_moving_a_grouped_tab_after_its_group_clamps_to_the_last_row(model: TabModel) -> None:
    tabs, group = grouped_pair_in_middle(model)
    model.moveTab(1, 3)
    assert [model.indexOfTab(tab) for tab in tabs] == [0, 2, 1, 3]
    assert tabs[1].group is group


def test_moving_an_ungrouped_tab_into_a_group_puts_it_at_the_nearest_edge(model: TabModel) -> None:
    tabs, _ = grouped_pair_in_middle(model)
    model.moveTab(3, 2)
    assert [model.indexOfTab(tab) for tab in tabs] == [0, 2, 3, 1]


def test_moving_never_changes_a_tab_group(model: TabModel) -> None:
    tabs, group = grouped_pair_in_middle(model)
    model.moveTab(0, 2)
    model.moveTab(3, 1)
    model.moveTab(1, 0)
    assert [tab.group for tab in tabs] == [None, group, group, None]


def test_stepping_an_ungrouped_tab_hops_over_a_whole_group(model: TabModel) -> None:
    tabs, _ = grouped_pair_in_middle(model)
    model.stepTab(0, 1)
    assert model.indexOfTab(tabs[0]) == LAST_OF_THREE


def test_restoring_a_split_group_gathers_its_tabs(model: TabModel) -> None:
    tabs = add_tabs(model, 4)
    model.restoreGroups([{"name": "g", "color": "green"}], [0, -1, 0, -1])
    assert [model.indexOfTab(tab) for tab in tabs] == [0, 2, 1, 3]
