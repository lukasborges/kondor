from kondor.browser.address.searchsuggestions import SearchSuggestions
from kondor.browser.favicons.faviconstore import FaviconStore
from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.zoommanager import ZoomManager
from kondor.core.qmlregistration import QmlKind, QmlType, register

QML_TYPES: tuple[QmlType, ...] = (
    QmlType(FaviconStore, "FaviconStore", QmlKind.SINGLETON),
    QmlType(ProfileManager, "ProfileManager", QmlKind.SINGLETON),
    QmlType(SearchSuggestions, "SearchSuggestions", QmlKind.SINGLETON),
    QmlType(ZoomManager, "ZoomManager", QmlKind.SINGLETON),
)


def register_types() -> None:
    register(QML_TYPES)
