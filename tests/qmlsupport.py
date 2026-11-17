from collections.abc import Iterator
from contextlib import contextmanager

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QObject,
    QtMsgType,
    QUrl,
    qInstallMessageHandler,
)
from PySide6.QtGui import QAccessible
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem

from kondor.browser.profile.profilemanager import ProfileManager


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


def is_unnamed_button(item: QQuickItem) -> bool:
    if not item.isVisible() or not item.inherits("QQuickAbstractButton"):
        return False
    accessible = QAccessible.queryAccessibleInterface(item)
    return accessible is not None and not accessible.text(QAccessible.Text.Name)


def unnamed_buttons(item: QQuickItem) -> list[str]:
    found = [item.metaObject().className()] if is_unnamed_button(item) else []
    for child in item.childItems():
        found += unnamed_buttons(child)
    return found


def drain_deferred_deletes() -> None:
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def release(*objects: QObject) -> None:
    for released in objects:
        released.deleteLater()
    drain_deferred_deletes()


def release_profiles() -> None:
    profiles = ProfileManager.instance()
    release(*[p for p in [*profiles._private_profiles, profiles._default_profile] if p])
    profiles._default_profile = None
