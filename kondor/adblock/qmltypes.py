from kondor.adblock.adblockmanager import AdBlockManager
from kondor.core.qmlregistration import QmlKind, QmlType, register

QML_TYPES: tuple[QmlType, ...] = (QmlType(AdBlockManager, "AdBlockManager", QmlKind.SINGLETON),)


def register_types() -> None:
    register(QML_TYPES)
