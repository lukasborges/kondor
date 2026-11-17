from typing import Any, Protocol

CdpParams = dict[str, Any]


class PageSession(Protocol):
    isolated_worlds: dict[str, int]

    def call(self, method: str, params: CdpParams | None = None) -> CdpParams: ...

    def clear_events(self) -> None: ...

    def wait_for_event(self, name: str, timeout_milliseconds: int) -> bool: ...
