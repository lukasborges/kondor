import pytest
from PySide6.QtCore import QObject

from kondor.browser.agent.agenttabs import AgentTabs
from kondor.browser.agent.tabagent import TabAgent

pytestmark = pytest.mark.usefixtures("qapp")


@pytest.fixture
def tabs() -> AgentTabs:
    return AgentTabs()


def watched_agent(tabs: AgentTabs, target_id: str, is_private: bool = False) -> TabAgent:
    agent = TabAgent(is_private)
    tabs.watch(agent)
    agent.setTargetId(target_id)
    return agent


def test_lists_only_tabs_with_agent_access(tabs: AgentTabs) -> None:
    watched_agent(tabs, "mine")
    handed_over = watched_agent(tabs, "shared")

    handed_over.allow()

    assert tabs.target_ids() == ["shared"]


def test_owns_a_tab_with_the_name_of_the_session(tabs: AgentTabs) -> None:
    agent = watched_agent(tabs, "T1")

    tabs.own("T1", "Claude Code")

    assert (agent.hasAccess, agent.name) == (True, "Claude Code")


def test_owns_a_tab_whose_target_id_arrives_later(tabs: AgentTabs) -> None:
    tabs.own("T2", "Claude Code")
    agent = TabAgent(False)
    tabs.watch(agent)

    agent.setTargetId("T2")

    assert (agent.hasAccess, agent.name) == (True, "Claude Code")


def test_announces_when_access_is_granted_and_removed(tabs: AgentTabs) -> None:
    changes: list[tuple[str, bool]] = []
    tabs.tabAccessChanged.connect(lambda target, access: changes.append((target, access)))
    agent = watched_agent(tabs, "T3")

    agent.allow()
    agent.remove()

    assert changes == [("T3", True), ("T3", False)]


def test_never_gives_access_to_a_private_tab(tabs: AgentTabs) -> None:
    agent = watched_agent(tabs, "T4", is_private=True)

    tabs.own("T4", "Claude Code")
    agent.allow()

    assert not agent.hasAccess


def test_a_tab_opened_by_an_agent_tab_inherits_its_access() -> None:
    opener, child, request = TabAgent(False), TabAgent(False), QObject()
    opener.grant("Claude Code")

    opener.passOnTo(request)
    child.inherit_for(request)

    assert (child.hasAccess, child.name) == (True, "Claude Code")


def test_a_tab_opened_by_a_normal_tab_has_no_access() -> None:
    opener, child, request = TabAgent(False), TabAgent(False), QObject()

    opener.passOnTo(request)
    child.inherit_for(request)

    assert not child.hasAccess


def test_shows_who_is_working_in_the_tab(tabs: AgentTabs) -> None:
    agent = watched_agent(tabs, "T5")
    agent.allow()

    tabs.note_activity("T5", "Claude Code")

    assert agent.workingName == "Claude Code"


def test_ignores_activity_in_a_tab_without_access(tabs: AgentTabs) -> None:
    agent = watched_agent(tabs, "T6")

    tabs.note_activity("T6", "Claude Code")

    assert agent.workingName == ""
