from collections.abc import Sequence
from enum import Enum
from typing import NamedTuple

from PySide6.QtCore import QObject
from PySide6.QtQml import (
    qmlRegisterSingletonInstance,
    qmlRegisterType,
    qmlRegisterUncreatableType,
)

MODULE_URI = "Kondor"
VERSION_MAJOR = 1
VERSION_MINOR = 0


class QmlKind(Enum):
    SINGLETON = "singleton"
    UNCREATABLE = "uncreatable"
    CREATABLE = "creatable"


class QmlType(NamedTuple):
    type_class: type[QObject]
    name: str
    kind: QmlKind


def uncreatable_reason(entry: QmlType) -> str:
    return f"{entry.name} cannot be created from QML"


def register_singleton(entry: QmlType) -> None:
    instance = entry.type_class.instance()  # type: ignore[attr-defined]
    qmlRegisterSingletonInstance(
        entry.type_class, MODULE_URI, VERSION_MAJOR, VERSION_MINOR, entry.name, instance
    )


def register_uncreatable(entry: QmlType) -> None:
    qmlRegisterUncreatableType(
        entry.type_class,
        MODULE_URI,
        VERSION_MAJOR,
        VERSION_MINOR,
        entry.name,
        uncreatable_reason(entry),
    )


def register_creatable(entry: QmlType) -> None:
    qmlRegisterType(entry.type_class, MODULE_URI, VERSION_MAJOR, VERSION_MINOR, entry.name)


REGISTRARS = {
    QmlKind.SINGLETON: register_singleton,
    QmlKind.UNCREATABLE: register_uncreatable,
    QmlKind.CREATABLE: register_creatable,
}


def register(types: Sequence[QmlType]) -> None:
    for entry in types:
        REGISTRARS[entry.kind](entry)
