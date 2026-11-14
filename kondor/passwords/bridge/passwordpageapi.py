from typing import Protocol

from PySide6.QtCore import QObject, Signal, Slot


class PageApiOwner(Protocol):
    def form_submitted(self, origin: str, username: str, password: str) -> None: ...

    def credentials_for(self, origin: str) -> list[dict[str, str]]: ...


class PasswordPageApi(QObject):
    credentialsChanged = Signal()
    fillRequested = Signal(str, str, str)

    def __init__(self, bridge: QObject, owner: PageApiOwner) -> None:
        super().__init__(bridge)
        self._owner = owner

    @Slot(str, str, str)
    def formSubmitted(self, origin: str, username: str, password: str) -> None:
        self._owner.form_submitted(origin, username, password)

    @Slot(str, result="QVariantList")
    def credentialsFor(self, origin: str) -> list[dict[str, str]]:
        return self._owner.credentials_for(origin)
