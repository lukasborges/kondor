from dataclasses import dataclass
from typing import Protocol

from kondor.app.mcp.cdp.pagesession import PageSession


@dataclass(frozen=True)
class PageInfo:
    id: str
    title: str
    url: str
    is_current: bool


class Browser(Protocol):
    def list_pages(self) -> list[PageInfo]: ...

    def page(self, page_id: str | None) -> PageSession: ...

    def open_tab(self, url: str) -> PageInfo: ...
