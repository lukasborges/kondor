from kondor.browser.address.searchsuggestions import SearchSuggestions
from kondor.browser.favicons.faviconstore import FaviconStore
from kondor.browser.media.mediabridge import MediaBridge
from kondor.browser.popups.popupbridge import PopupBridge
from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.session.sessionmanager import SessionManager
from kondor.browser.tabs.features.tabextensionitems import TabExtensionItems
from kondor.browser.tabs.features.tabmedia import TabMedia
from kondor.browser.tabs.features.tabpasswords import TabPasswords
from kondor.browser.tabs.features.tabpasswordsuggestion import TabPasswordSuggestion
from kondor.browser.tabs.features.tabpermissions import TabPermissions
from kondor.browser.tabs.features.tabpopups import TabPopups
from kondor.browser.tabs.features.tabsecurity import TabSecurity
from kondor.browser.tabs.features.tabsitereload import TabSiteReload
from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from kondor.browser.zoommanager import ZoomManager
from kondor.core.qmlregistration import QmlKind, QmlType, register
from kondor.site.identity.tabidentity import TabIdentity

QML_TYPES: tuple[QmlType, ...] = (
    QmlType(FaviconStore, "FaviconStore", QmlKind.SINGLETON),
    QmlType(MediaBridge, "MediaBridge", QmlKind.CREATABLE),
    QmlType(PopupBridge, "PopupBridge", QmlKind.CREATABLE),
    QmlType(ProfileManager, "ProfileManager", QmlKind.SINGLETON),
    QmlType(SearchSuggestions, "SearchSuggestions", QmlKind.SINGLETON),
    QmlType(SessionManager, "SessionManager", QmlKind.SINGLETON),
    QmlType(Tab, "Tab", QmlKind.UNCREATABLE),
    QmlType(TabSecurity, "TabSecurity", QmlKind.UNCREATABLE),
    QmlType(TabPermissions, "TabPermissions", QmlKind.UNCREATABLE),
    QmlType(TabPasswords, "TabPasswords", QmlKind.UNCREATABLE),
    QmlType(TabPasswordSuggestion, "TabPasswordSuggestion", QmlKind.UNCREATABLE),
    QmlType(TabSiteReload, "TabSiteReload", QmlKind.UNCREATABLE),
    QmlType(TabExtensionItems, "TabExtensionItems", QmlKind.UNCREATABLE),
    QmlType(TabMedia, "TabMedia", QmlKind.UNCREATABLE),
    QmlType(TabIdentity, "TabIdentity", QmlKind.UNCREATABLE),
    QmlType(TabPopups, "TabPopups", QmlKind.UNCREATABLE),
    QmlType(TabModel, "TabModel", QmlKind.CREATABLE),
    QmlType(ZoomManager, "ZoomManager", QmlKind.SINGLETON),
)


def register_types() -> None:
    register(QML_TYPES)
