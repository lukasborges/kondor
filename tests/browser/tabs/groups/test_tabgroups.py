import pytest

from kondor.browser.tabs.groups.tabgroup import GROUP_COLORS
from kondor.browser.tabs.tabmodel import TabModel

pytestmark = pytest.mark.no_qt_log

LAST_OF_THREE = 2
TWO_TABS = 2
AFTER_OTHER_GROUP = 3


def add_tabs(model: TabModel, count: int) -> list:
    return [model.addTab() for _ in range(count)]


def test_new_group_takes_the_first_unused_color(model: TabModel) -> None:
    add_tabs(model, 3)
    first = model.newGroupForTab(0)
    second = model.newGroupForTab(1)
    assert [first.color, second.color] == [GROUP_COLORS[0], GROUP_COLORS[1]]


def test_adding_a_tab_moves_it_to_the_end_of_the_group(model: TabModel) -> None:
    tabs = add_tabs(model, 4)
    group = model.newGroupForTab(0)
    model.addTabToGroup(1, group)
    model.addTabToGroup(3, group)
    assert [model.indexOfTab(tab) for tab in tabs] == [0, 1, 3, 2]
    assert tabs[3].group is group


def test_adding_an_earlier_tab_moves_it_after_the_group(model: TabModel) -> None:
    tabs = add_tabs(model, 3)
    group = model.newGroupForTab(1)
    model.addTabToGroup(2, group)
    model.addTabToGroup(0, group)
    assert [model.indexOfTab(tab) for tab in tabs] == [2, 0, 1]


def test_removing_a_middle_tab_keeps_the_group_contiguous(model: TabModel) -> None:
    tabs = add_tabs(model, 3)
    group = model.newGroupForTab(0)
    model.addTabToGroup(1, group)
    model.addTabToGroup(2, group)
    model.removeTabFromGroup(0)
    assert tabs[0].group is None
    assert model.indexOfTab(tabs[0]) == LAST_OF_THREE


def test_group_without_tabs_is_deleted(model: TabModel) -> None:
    add_tabs(model, 2)
    model.newGroupForTab(0)
    model.closeTab(0)
    assert model.groups == []


def test_pinning_a_grouped_tab_takes_it_out_of_the_group(model: TabModel) -> None:
    tabs = add_tabs(model, 2)
    model.newGroupForTab(0)
    model.setPinned(0, True)
    assert tabs[0].group is None
    assert model.groups == []


def test_pinned_tabs_cannot_join_groups(model: TabModel) -> None:
    add_tabs(model, 2)
    model.setPinned(0, True)
    assert model.newGroupForTab(0) is None


def test_moving_a_tab_between_group_members_joins_the_group(model: TabModel) -> None:
    tabs = add_tabs(model, 4)
    group = model.newGroupForTab(0)
    model.addTabToGroup(1, group)
    model.moveTab(3, 1)
    assert tabs[3].group is group


def test_moving_a_tab_out_of_the_group_leaves_it(model: TabModel) -> None:
    tabs = add_tabs(model, 3)
    group = model.newGroupForTab(0)
    model.addTabToGroup(1, group)
    model.moveTab(0, 2)
    assert tabs[0].group is None
    assert tabs[1].group is group


def test_collapsing_the_current_group_selects_the_next_tab_outside(model: TabModel) -> None:
    tabs = add_tabs(model, 3)
    group = model.newGroupForTab(0)
    model.addTabToGroup(1, group)
    model.setCurrentIndex(0)
    model.setGroupCollapsed(group, True)
    assert group.collapsed
    assert model.currentTab is tabs[2]


def test_collapsing_the_current_group_selects_the_previous_tab_at_the_end(model: TabModel) -> None:
    tabs = add_tabs(model, 3)
    group = model.newGroupForTab(1)
    model.addTabToGroup(2, group)
    model.setGroupCollapsed(group, True)
    assert model.currentTab is tabs[0]


def test_group_holding_every_tab_does_not_collapse(model: TabModel) -> None:
    add_tabs(model, 2)
    group = model.newGroupForTab(0)
    model.addTabToGroup(1, group)
    model.setGroupCollapsed(group, True)
    assert not group.collapsed


def test_activating_a_tab_of_a_collapsed_group_expands_it(model: TabModel) -> None:
    add_tabs(model, 3)
    group = model.newGroupForTab(0)
    model.setCurrentIndex(2)
    model.setGroupCollapsed(group, True)
    model.setCurrentIndex(0)
    assert not group.collapsed


def test_ungroup_keeps_the_tabs(model: TabModel) -> None:
    add_tabs(model, 2)
    group = model.newGroupForTab(0)
    model.addTabToGroup(1, group)
    model.ungroup(group)
    assert model.count == TWO_TABS
    assert model.groups == []


def test_closing_a_group_closes_its_tabs(model: TabModel) -> None:
    add_tabs(model, 3)
    group = model.newGroupForTab(1)
    model.addTabToGroup(2, group)
    model.closeGroup(group)
    assert model.count == 1


def test_moving_a_group_moves_all_its_tabs(model: TabModel) -> None:
    tabs = add_tabs(model, 4)
    group = model.newGroupForTab(0)
    model.addTabToGroup(1, group)
    model.moveGroup(group, 2)
    assert [model.indexOfTab(tab) for tab in tabs] == [2, 3, 0, 1]


def test_moving_a_group_does_not_land_inside_another_group(model: TabModel) -> None:
    tabs = add_tabs(model, 5)
    moved = model.newGroupForTab(0)
    other = model.newGroupForTab(1)
    model.addTabToGroup(2, other)
    model.addTabToGroup(3, other)
    model.moveGroup(moved, 2)
    assert model.indexOfTab(tabs[0]) == AFTER_OTHER_GROUP


def test_new_tab_in_group_joins_it(model: TabModel) -> None:
    add_tabs(model, 2)
    group = model.newGroupForTab(0)
    tab = model.newTabInGroup(group)
    assert tab.group is group
    assert model.indexOfTab(tab) == 1


def test_restore_groups_assigns_tabs_by_position(model: TabModel) -> None:
    tabs = add_tabs(model, 3)
    model.restoreGroups([{"name": "Work", "color": "red", "collapsed": True}], [-1, 0, 0])
    assert tabs[0].group is None
    assert tabs[1].group is tabs[2].group
    assert (tabs[1].group.name, tabs[1].group.color) == ("Work", "red")
    assert tabs[1].group.collapsed
