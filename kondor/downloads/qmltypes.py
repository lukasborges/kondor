from kondor.core.qmlregistration import QmlKind, QmlType, register
from kondor.downloads.downloadmanager import DownloadManager
from kondor.downloads.downloadmodel import DownloadModel

QML_TYPES: tuple[QmlType, ...] = (
    QmlType(DownloadManager, "DownloadManager", QmlKind.SINGLETON),
    QmlType(DownloadModel, "DownloadModel", QmlKind.UNCREATABLE),
)


def register_types() -> None:
    register(QML_TYPES)
