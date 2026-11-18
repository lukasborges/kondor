from typing import ClassVar

from PySide6.QtCore import QCoreApplication, QObject, Slot

from kondor.app.instance.singleinstance import SingleInstance
from kondor.app.restart.restartlaunch import start_again
from kondor.browser.session.sessionmanager import SessionManager


class AppRestart(QObject):
    _instance: ClassVar["AppRestart | None"] = None

    def __init__(self) -> None:
        super().__init__()
        self._is_pending = False

    @classmethod
    def instance(cls) -> "AppRestart":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def is_pending(self) -> bool:
        return self._is_pending

    @Slot()
    def restart(self) -> None:
        SessionManager.instance().save_now()
        self._is_pending = True
        QCoreApplication.quit()

    def start_again_when_pending(self, single_instance: SingleInstance) -> None:
        if not self._is_pending:
            return
        single_instance.close()
        start_again()
