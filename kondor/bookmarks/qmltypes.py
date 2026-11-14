from kondor.bookmarks.bookmarkmanager import BookmarkManager
from kondor.bookmarks.bookmarkmodel import BookmarkModel
from kondor.core.qmlregistration import QmlKind, QmlType, register

QML_TYPES: tuple[QmlType, ...] = (
    QmlType(BookmarkManager, "BookmarkManager", QmlKind.SINGLETON),
    QmlType(BookmarkModel, "BookmarkModel", QmlKind.UNCREATABLE),
)


def register_types() -> None:
    register(QML_TYPES)
