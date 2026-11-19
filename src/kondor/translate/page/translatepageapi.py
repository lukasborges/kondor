from typing import Protocol

from PySide6.QtCore import QObject, Slot


class PageReportOwner(Protocol):
    def receive_language(self, declared: str, sample: str) -> None: ...

    def receive_batch(self, batch_id: int, texts_json: str) -> None: ...

    def receive_state(self, state: str) -> None: ...


class TranslatePageApi(QObject):
    def __init__(self, bridge: QObject, owner: PageReportOwner) -> None:
        super().__init__(bridge)
        self._owner = owner

    @Slot(str, str)
    def reportLanguage(self, declared: str, sample: str) -> None:
        self._owner.receive_language(declared, sample)

    @Slot(int, str)
    def requestBatch(self, batch_id: int, texts_json: str) -> None:
        self._owner.receive_batch(batch_id, texts_json)

    @Slot(str)
    def reportState(self, state: str) -> None:
        self._owner.receive_state(state)
