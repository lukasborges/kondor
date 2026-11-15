from PySide6.QtNetwork import QHostAddress, QTcpServer

MIN_PORT = 1024
MAX_PORT = 65535


def parse_port(text: str) -> int | None:
    if not text.isdigit():
        return None
    port = int(text)
    return port if MIN_PORT <= port <= MAX_PORT else None


def requested_port(option_port: int | None, is_enabled: bool, stored_port: int) -> int | None:
    if option_port is not None:
        return option_port
    return stored_port if is_enabled else None


def is_port_free(port: int) -> bool:
    server = QTcpServer()
    is_free = server.listen(QHostAddress.SpecialAddress.LocalHost, port)
    server.close()
    return bool(is_free)
