from kondor.core.qmlregistration import QmlKind, QmlType, register
from kondor.extensions.extensionmanager import ExtensionManager

QML_TYPES: tuple[QmlType, ...] = (QmlType(ExtensionManager, "ExtensionManager", QmlKind.SINGLETON),)


def register_types() -> None:
    register(QML_TYPES)
