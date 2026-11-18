import pytest

from kondor.app.instance.sessionprotocol import ClientIdentity
from kondor.app.mcp.cdp.pagetargets import PageTarget
from kondor.app.mcp.protocol.toolresult import ToolFailureError
from kondor.app.mcp.session.remotebrowser import NOT_AN_AGENT_TAB, RemoteBrowser

pytestmark = pytest.mark.usefixtures("qapp")


def target(target_id: str) -> PageTarget:
    return PageTarget(target_id, target_id, f"https://{target_id}.example/", "ws://x")


class FakeLink:
    def __init__(self, agent_ids: set[str]) -> None:
        self.agent_ids = agent_ids
        self.owned: list[str] = []

    def is_closed(self) -> bool:
        return False

    def agent_tab_ids(self) -> set[str]:
        return set(self.agent_ids)

    def add_agent_tab(self, target_id: str) -> None:
        self.owned.append(target_id)
        self.agent_ids.add(target_id)

    def announce_ports(self, ports: list[int]) -> None:
        return None


class FakeLister:
    def __init__(self, pages: list[PageTarget]) -> None:
        self.pages = pages

    def list_pages(self) -> list[PageTarget]:
        return self.pages


def browser_with(link: FakeLink, ids: list[str]) -> RemoteBrowser:
    browser = RemoteBrowser(link, lambda url: True)  # type: ignore[arg-type]
    browser._lister = FakeLister([target(i) for i in ids])  # type: ignore[assignment]
    browser.is_visible = lambda page: False  # type: ignore[method-assign]
    browser.connection_for = lambda page: page  # type: ignore[method-assign,assignment]
    browser.set_client(ClientIdentity("Claude Code", "1"))
    return browser


def test_lists_only_the_agent_tabs() -> None:
    browser = browser_with(FakeLink({"B"}), ["A", "B", "C"])

    assert [page.id for page in browser.list_pages()] == ["B"]


def test_refuses_a_tab_that_is_not_open_to_agents() -> None:
    browser = browser_with(FakeLink({"B"}), ["A", "B"])

    with pytest.raises(ToolFailureError, match=NOT_AN_AGENT_TAB):
        browser.page("A")


def test_refuses_the_default_page_when_no_tab_is_open_to_agents() -> None:
    browser = browser_with(FakeLink(set()), ["A"])

    with pytest.raises(ToolFailureError, match="new_tab"):
        browser.page(None)


def test_defaults_to_the_agent_tab_used_last() -> None:
    browser = browser_with(FakeLink({"A", "B"}), ["A", "B"])
    browser.page("B")

    assert browser.page(None).id == "B"  # type: ignore[attr-defined]


def test_takes_ownership_of_a_tab_it_opened() -> None:
    link = FakeLink(set())
    browser = browser_with(link, [])

    browser.take_ownership(target("N"))

    assert link.owned == ["N"]


def test_ignores_new_targets_that_have_no_page_yet() -> None:
    browser = browser_with(FakeLink(set()), [])
    blank = PageTarget("E", "", "", "ws://x")
    browser._lister = FakeLister([blank, target("N")])  # type: ignore[assignment]

    assert [page.id for page in browser.new_targets(set())] == ["N"]
