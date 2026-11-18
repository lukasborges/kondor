from PySide6.QtCore import QObject

_names_by_request: dict[int, str] = {}


def remember(request: QObject, name: str) -> None:
    _names_by_request[id(request)] = name


def take(request: QObject) -> str | None:
    return _names_by_request.pop(id(request), None)
