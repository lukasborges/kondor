from kondor.browser.favicons.faviconstore import FaviconStore
from kondor.core.qmlregistration import QmlKind, QmlType, register

QML_TYPES: tuple[QmlType, ...] = (QmlType(FaviconStore, "FaviconStore", QmlKind.SINGLETON),)


def register_types() -> None:
    register(QML_TYPES)
