from kondor.core.qmlregistration import QmlKind, QmlType, register
from kondor.site.sitesettings import SiteSettings

QML_TYPES: tuple[QmlType, ...] = (QmlType(SiteSettings, "SiteSettings", QmlKind.SINGLETON),)


def register_types() -> None:
    register(QML_TYPES)
