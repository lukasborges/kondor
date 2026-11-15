from kondor.core.qmlregistration import QmlKind, QmlType, register
from kondor.passwords.bridge.passwordbridge import PasswordBridge
from kondor.passwords.passwordstore import PasswordStore

QML_TYPES: tuple[QmlType, ...] = (
    QmlType(PasswordBridge, "PasswordBridge", QmlKind.CREATABLE),
    QmlType(PasswordStore, "PasswordStore", QmlKind.SINGLETON),
)


def register_types() -> None:
    register(QML_TYPES)
