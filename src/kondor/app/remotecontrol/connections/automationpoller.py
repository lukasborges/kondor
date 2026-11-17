from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QObject, QTimer

from kondor.app.remotecontrol.connections import proctcp
from kondor.app.remotecontrol.connections.connection import AUTOMATION_TOOL_NAME, Connection
from kondor.app.remotecontrol.connections.connectionmodel import ConnectionModel
from kondor.app.remotecontrol.connections.proctcp import StablePorts

POLL_MILLISECONDS = 2000
PROC_TABLE = Path("/proc/net/tcp")


def read_table() -> str:
    try:
        return PROC_TABLE.read_text()
    except OSError:
        return ""


class AutomationPoller(QObject):
    def __init__(
        self, model: ConnectionModel, port: int, table: Callable[[], str] = read_table
    ) -> None:
        super().__init__(model)
        self._model = model
        self._port = port
        self._table = table
        self._stable = StablePorts()
        self._timer = QTimer(self)
        self._timer.setInterval(POLL_MILLISECONDS)
        self._timer.timeout.connect(self.poll)

    def start(self) -> None:
        self._timer.start()

    def poll(self) -> None:
        current = proctcp.remote_ports(self._table(), self._port) - self._model.session_ports()
        self.show_automation(bool(self._stable.update(current)))

    def show_automation(self, is_present: bool) -> None:
        shown = self._model.find_automation()
        if is_present and shown is None:
            self._model.add(Connection(AUTOMATION_TOOL_NAME))
        elif not is_present and shown is not None:
            self._model.remove(shown)
