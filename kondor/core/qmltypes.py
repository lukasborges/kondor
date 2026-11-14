from kondor.core.filehelper import FileHelper
from kondor.core.notifier import Notifier
from kondor.core.qmlregistration import QmlKind, QmlType, register
from kondor.core.settings.settings import Settings

QML_TYPES: tuple[QmlType, ...] = (
    QmlType(FileHelper, "FileHelper", QmlKind.SINGLETON),
    QmlType(Notifier, "Notifier", QmlKind.SINGLETON),
    QmlType(Settings, "Settings", QmlKind.SINGLETON),
)


def register_types() -> None:
    register(QML_TYPES)
