import os
import sys
from collections.abc import Callable

from PySide6.QtCore import QObject, QSocketNotifier, Signal

from kondor.app.mcp.protocol import jsonrpc
from kondor.app.mcp.protocol.dispatcher import Dispatcher

READ_SIZE = 65536
Output = Callable[[bytes], None]


def write_to_stdout(data: bytes) -> None:
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


class StdioServer(QObject):
    finished = Signal()

    def __init__(
        self, dispatcher: Dispatcher, input_descriptor: int = 0, output: Output = write_to_stdout
    ) -> None:
        super().__init__()
        self._dispatcher = dispatcher
        self._descriptor = input_descriptor
        self._output = output
        self._buffer = b""
        self._notifier = QSocketNotifier(input_descriptor, QSocketNotifier.Type.Read, self)
        self._notifier.activated.connect(self.read_available)

    def read_available(self) -> None:
        data = os.read(self._descriptor, READ_SIZE)
        if not data:
            self._notifier.setEnabled(False)
            self.finished.emit()
            return
        self._buffer += data
        self.process_lines()

    def process_lines(self) -> None:
        self._notifier.setEnabled(False)
        *lines, self._buffer = self._buffer.split(b"\n")
        for line in lines:
            self.process_line(line)
        self._notifier.setEnabled(True)

    def process_line(self, line: bytes) -> None:
        if not line.strip():
            return
        message = jsonrpc.parse_line(line)
        response = self.answer(message)
        if response is not None:
            self._output(jsonrpc.encode_line(response))

    def answer(self, message: jsonrpc.JsonObject | None) -> jsonrpc.JsonObject | None:
        if message is None:
            return jsonrpc.failure(None, jsonrpc.PARSE_ERROR, "parse error")
        return self._dispatcher.handle(message)
