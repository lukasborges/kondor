from kondor.core.qmlregistration import QmlKind, QmlType, register
from kondor.site.identity.browseridentity import BrowserIdentity
from kondor.site.sitesettings import SiteSettings

QML_TYPES: tuple[QmlType, ...] = (
    QmlType(BrowserIdentity, "BrowserIdentity", QmlKind.SINGLETON),
    QmlType(SiteSettings, "SiteSettings", QmlKind.SINGLETON),
)


def register_types() -> None:
    register(QML_TYPES)
