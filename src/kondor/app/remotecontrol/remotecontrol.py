import os
from typing import ClassVar

from PySide6.QtCore import Property, QObject, Slot
from PySide6.QtGui import QGuiApplication

from kondor.app.instance.sessionprotocol import RemoteControlState
from kondor.app.instance.singleinstance import SingleInstance
from kondor.app.remotecontrol import mcpcommand
from kondor.app.remotecontrol.connections.automationpoller import AutomationPoller
from kondor.app.remotecontrol.connections.connectionmodel import ConnectionModel
from kondor.app.remotecontrol.connections.sessionregistry import SessionRegistry
from kondor.app.remotecontrol.remotecontrolenvironment import LOCAL_HOST


class RemoteControl(QObject):
    _instance: ClassVar["RemoteControl | None"] = None

    def __init__(self) -> None:
        super().__init__()
        self._port: int | None = None
        self._is_requested_on_command_line = False
        self._connections = ConnectionModel(self)
        self._sessions = SessionRegistry(self._connections)

    @classmethod
    def instance(cls) -> "RemoteControl":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_port(self, port: int | None, is_requested_on_command_line: bool = False) -> None:
        self._port = port
        self._is_requested_on_command_line = is_requested_on_command_line
        self._sessions.state = RemoteControlState(port is not None, port or 0)

    def watch(self, single_instance: SingleInstance) -> None:
        single_instance.sessionLineReceived.connect(self._sessions.handle_line)
        if self._port is not None:
            AutomationPoller(self._connections, self._port).start()

    def is_requested_on_command_line(self) -> bool:
        return self._is_requested_on_command_line

    def port_number(self) -> int:
        return self._port or 0

    def is_active(self) -> bool:
        return self._port is not None

    def address_text(self) -> str:
        return f"http://{LOCAL_HOST}:{self._port}" if self._port is not None else ""

    def connection_model(self) -> ConnectionModel:
        return self._connections

    def mcp_command_text(self) -> str:
        return mcpcommand.command_text(mcpcommand.mcp_words(os.environ))

    @Slot()
    def copyAddress(self) -> None:
        QGuiApplication.clipboard().setText(self.address_text())

    @Slot()
    def copyMcpCommand(self) -> None:
        QGuiApplication.clipboard().setText(self.mcp_command_text())

    active = Property(bool, is_active, constant=True)
    address = Property(str, address_text, constant=True)
    port = Property(int, port_number, constant=True)
    requestedOnCommandLine = Property(bool, is_requested_on_command_line, constant=True)
    connections = Property(QObject, connection_model, constant=True)
    mcpCommand = Property(str, mcp_command_text, constant=True)
