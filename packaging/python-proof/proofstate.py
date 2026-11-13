from typing import ClassVar

from interceptor import BlockingInterceptor
from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile


class ProofState(QObject):
    _instance: ClassVar["ProofState | None"] = None
    reported = Signal(str, bool, str)

    def __init__(self) -> None:
        super().__init__()
        self._interceptor = BlockingInterceptor()
        self._profile = QQuickWebEngineProfile(self)
        self._profile.setUrlRequestInterceptor(self._interceptor)

    @classmethod
    def instance(cls) -> "ProofState":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @Property(QObject, constant=True)  # type: ignore[arg-type]
    def profile(self) -> QQuickWebEngineProfile:
        return self._profile

    @property
    def interceptor(self) -> BlockingInterceptor:
        return self._interceptor

    @Slot(str, bool, str)
    def report(self, name: str, passed: bool, reason: str) -> None:
        self.reported.emit(name, passed, reason)
