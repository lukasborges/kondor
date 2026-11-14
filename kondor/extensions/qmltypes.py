from kondor.core.qmlregistration import QmlKind, QmlType, register
from kondor.extensions.catalog.extensioncatalog import ExtensionCatalog
from kondor.extensions.extensionmanager import ExtensionManager

QML_TYPES: tuple[QmlType, ...] = (
    QmlType(ExtensionManager, "ExtensionManager", QmlKind.SINGLETON),
    QmlType(ExtensionCatalog, "ExtensionCatalog", QmlKind.SINGLETON),
)


def register_types() -> None:
    register(QML_TYPES)
