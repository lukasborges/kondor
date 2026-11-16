from typing import Protocol

from PySide6.QtCore import QObject, Signal, Slot

FieldInfo = dict[str, object]


class PageApiOwner(Protocol):
    def form_submitted(self, origin: str, username: str, password: str) -> None: ...

    def credentials_for(self, origin: str) -> list[dict[str, str]]: ...

    def password_field_focused(self, field: FieldInfo) -> None: ...

    def password_field_left(self) -> None: ...

    def generate_password(self, rules: FieldInfo) -> str: ...

    def generated_password_filled(self, origin: str, password: str) -> None: ...


class PasswordPageApi(QObject):
    credentialsChanged = Signal()
    fillRequested = Signal(str, str, str)
    generateRequested = Signal()

    def __init__(self, bridge: QObject, owner: PageApiOwner) -> None:
        super().__init__(bridge)
        self._owner = owner

    @Slot(str, str, str)
    def formSubmitted(self, origin: str, username: str, password: str) -> None:
        self._owner.form_submitted(origin, username, password)

    @Slot(str, result="QVariantList")
    def credentialsFor(self, origin: str) -> list[dict[str, str]]:
        return self._owner.credentials_for(origin)

    @Slot("QVariantMap")
    def passwordFieldFocused(self, field: FieldInfo) -> None:
        self._owner.password_field_focused(field)

    @Slot()
    def passwordFieldLeft(self) -> None:
        self._owner.password_field_left()

    @Slot("QVariantMap", result=str)
    def generatePassword(self, rules: FieldInfo) -> str:
        return self._owner.generate_password(rules)

    @Slot(str, str)
    def generatedPasswordFilled(self, origin: str, password: str) -> None:
        self._owner.generated_password_filled(origin, password)
