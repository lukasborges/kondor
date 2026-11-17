from typing import Any

from kondor.app.mcp.cdp.pagesession import CdpParams
from kondor.app.mcp.tools.browser import PageInfo


class FakeSession:
    def __init__(self, replies: dict[str, CdpParams] | None = None) -> None:
        self.isolated_worlds: dict[str, int] = {}
        self.calls: list[tuple[str, CdpParams]] = []
        self.events: list[str] = ["Page.loadEventFired"]
        self._replies = replies or {}

    def call(self, method: str, params: CdpParams | None = None) -> CdpParams:
        self.calls.append((method, params or {}))
        return self._replies.get(method, {})

    def clear_events(self) -> None:
        return None

    def wait_for_event(self, name: str, timeout_milliseconds: int) -> bool:
        return name in self.events

    def methods(self) -> list[str]:
        return [method for method, _ in self.calls]

    def params_of(self, method: str) -> list[CdpParams]:
        return [params for name, params in self.calls if name == method]


class FakeBrowser:
    def __init__(self, session: FakeSession) -> None:
        self.session = session
        self.requested_page: Any = "unset"
        self.opened: list[str] = []

    def list_pages(self) -> list[PageInfo]:
        return [
            PageInfo("A", "KDE", "https://kde.org/", True),
            PageInfo("B", "", "about:blank", False),
        ]

    def page(self, page_id: str | None) -> FakeSession:
        self.requested_page = page_id
        return self.session

    def open_tab(self, url: str) -> PageInfo:
        self.opened.append(url)
        return PageInfo("C", "", url, True)


WORLD_REPLIES: dict[str, CdpParams] = {
    "Page.getFrameTree": {"frameTree": {"frame": {"id": "frame-1"}}},
    "Page.createIsolatedWorld": {"executionContextId": 7},
}
