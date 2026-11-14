from kondor.core.qmlregistration import QmlKind, QmlType, register
from kondor.passwords.passwordstore import PasswordStore

QML_TYPES: tuple[QmlType, ...] = (QmlType(PasswordStore, "PasswordStore", QmlKind.SINGLETON),)


def register_types() -> None:
    register(QML_TYPES)
