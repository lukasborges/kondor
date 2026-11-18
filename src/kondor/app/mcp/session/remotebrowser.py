from collections.abc import Callable

from PySide6.QtCore import QObject

from kondor.app.instance.sessionprotocol import ClientIdentity
from kondor.app.mcp.cdp.blocking import wait_until
from kondor.app.mcp.cdp.cdpconnection import CdpConnection, PointerAnnouncer
from kondor.app.mcp.cdp.pagesession import PageSession
from kondor.app.mcp.cdp.pagetargets import PageTarget, TargetLister
from kondor.app.mcp.protocol.toolresult import ToolFailureError
from kondor.app.mcp.session.browserlink import BrowserLink
from kondor.app.mcp.tools.browser import PageInfo

REMOTE_CONTROL_OFF = (
    "Remote control is off. Turn it on in Kondor's Settings → Privacy, then restart Kondor."
)
NOT_REACHABLE = "Kondor could not be started."
NOT_AN_AGENT_TAB = (
    "This tab is not open to agents. Open one with new_tab, "
    "or ask the user to choose Allow Agent Access on it."
)
NEW_TAB_TIMEOUT_MILLISECONDS = 5000


class RemoteBrowser(QObject):
    def __init__(self, link: BrowserLink, open_url: Callable[[str], bool]) -> None:
        super().__init__()
        self._link = link
        self._open_url = open_url
        self._client = ClientIdentity("", "")
        self._lister: TargetLister | None = None
        self._connections: dict[str, CdpConnection] = {}
        self._last_used_id = ""

    def set_client(self, client: ClientIdentity) -> None:
        self._client = client

    def lister(self) -> TargetLister:
        if self._lister is None or self._link.is_closed():
            self._lister = self.start_session()
        return self._lister

    def start_session(self) -> TargetLister:
        if self._link.is_closed():
            raise ToolFailureError("The session with Kondor ended.")
        state = self._link.open_session(self._client)
        if state is None:
            raise ToolFailureError(NOT_REACHABLE)
        if not state.is_active:
            raise ToolFailureError(REMOTE_CONTROL_OFF)
        return TargetLister(state.port)

    def agent_pages(self) -> list[PageTarget]:
        pages = self.lister().list_pages()
        agent_ids = self._link.agent_tab_ids()
        return [target for target in pages if target.id in agent_ids]

    def list_pages(self) -> list[PageInfo]:
        targets = self.agent_pages()
        current = self.current_target(targets)
        return [PageInfo(t.id, t.title, t.url, t is current) for t in targets]

    def current_target(self, targets: list[PageTarget]) -> PageTarget | None:
        visible = [target for target in targets if self.is_visible(target)]
        return visible[0] if visible else None

    def is_visible(self, target: PageTarget) -> bool:
        reply = self.connection_for(target).call(
            "Runtime.evaluate", {"expression": "document.visibilityState", "returnByValue": True}
        )
        return bool(reply.get("result", {}).get("value") == "visible")

    def page(self, page_id: str | None) -> PageSession:
        target = self.find_target(self.agent_pages(), page_id)
        self._last_used_id = target.id
        return self.connection_for(target)

    def find_target(self, targets: list[PageTarget], page_id: str | None) -> PageTarget:
        if page_id is None:
            return self.default_target(targets)
        for target in targets:
            if target.id == page_id:
                return target
        raise ToolFailureError(NOT_AN_AGENT_TAB)

    def default_target(self, targets: list[PageTarget]) -> PageTarget:
        last_used = [target for target in targets if target.id == self._last_used_id]
        if last_used:
            return last_used[0]
        if not targets:
            raise ToolFailureError(NOT_AN_AGENT_TAB)
        return self.current_target(targets) or targets[0]

    def connection_for(self, target: PageTarget) -> CdpConnection:
        known = self._connections.get(target.id)
        if known is not None and known.is_open():
            return known
        connection = CdpConnection(target.socket_url, self.pointer_announcer(target.id))
        if not connection.open():
            raise ToolFailureError(f"Could not attach to page {target.id}.")
        self._connections[target.id] = connection
        self._link.announce_ports(self.local_ports())
        return connection

    def pointer_announcer(self, target_id: str) -> PointerAnnouncer:
        return lambda kind, point: self._link.announce_pointer(target_id, kind, point)

    def local_ports(self) -> list[int]:
        return [connection.local_port() for connection in self._connections.values()]

    def open_tab(self, url: str) -> PageInfo:
        known = {target.id for target in self.lister().list_pages()}
        if not self._open_url(url):
            raise ToolFailureError(NOT_REACHABLE)
        wait_until(lambda: bool(self.new_targets(known)), NEW_TAB_TIMEOUT_MILLISECONDS)
        opened = self.new_targets(known)
        if not opened:
            raise ToolFailureError("Kondor did not open the tab.")
        return self.take_ownership(opened[0])

    def take_ownership(self, target: PageTarget) -> PageInfo:
        self._link.add_agent_tab(target.id)
        self._last_used_id = target.id
        return PageInfo(target.id, target.title, target.url, True)

    def new_targets(self, known: set[str]) -> list[PageTarget]:
        added = [target for target in self.lister().list_pages() if target.id not in known]
        return [target for target in added if target.url]
