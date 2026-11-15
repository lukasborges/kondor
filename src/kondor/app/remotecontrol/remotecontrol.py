from typing import ClassVar

from PySide6.QtCore import Property, QObject, Slot
from PySide6.QtGui import QGuiApplication

from kondor.app.remotecontrol.remotecontrolenvironment import LOCAL_HOST


class RemoteControl(QObject):
    _instance: ClassVar["RemoteControl | None"] = None

    def __init__(self) -> None:
        super().__init__()
        self._port: int | None = None
        self._is_requested_on_command_line = False

    @classmethod
    def instance(cls) -> "RemoteControl":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_port(self, port: int | None, is_requested_on_command_line: bool = False) -> None:
        self._port = port
        self._is_requested_on_command_line = is_requested_on_command_line

    def is_requested_on_command_line(self) -> bool:
        return self._is_requested_on_command_line

    def port_number(self) -> int:
        return self._port or 0

    def is_active(self) -> bool:
        return self._port is not None

    def address_text(self) -> str:
        return f"http://{LOCAL_HOST}:{self._port}" if self._port is not None else ""

    @Slot()
    def copyAddress(self) -> None:
        QGuiApplication.clipboard().setText(self.address_text())

    active = Property(bool, is_active, constant=True)
    address = Property(str, address_text, constant=True)
    port = Property(int, port_number, constant=True)
    requestedOnCommandLine = Property(bool, is_requested_on_command_line, constant=True)
