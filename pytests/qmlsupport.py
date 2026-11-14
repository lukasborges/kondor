from collections.abc import Iterator
from contextlib import contextmanager

from PySide6.QtCore import QObject, QtMsgType, QUrl, qInstallMessageHandler
from PySide6.QtQml import QQmlComponent, QQmlEngine


@contextmanager
def captured_messages() -> Iterator[list[str]]:
    messages: list[str] = []

    def record(mode: QtMsgType, context: object, message: str) -> None:
        messages.append(message)

    previous = qInstallMessageHandler(record)
    try:
        yield messages
    finally:
        qInstallMessageHandler(previous)


def load_component(engine: QQmlEngine, source: str) -> QQmlComponent:
    component = QQmlComponent(engine)
    component.setData(source.encode(), QUrl("inline.qml"))
    return component


def error_text(component: QQmlComponent) -> str:
    return "\n".join(error.toString() for error in component.errors())


def create_object(engine: QQmlEngine, source: str) -> QObject:
    component = load_component(engine, source)
    created = component.create()
    assert created is not None, error_text(component)
    return created
