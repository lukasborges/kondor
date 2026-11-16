from kondor.core.qmlregistration import QmlKind, QmlType, register
from kondor.profiles.userprofiles import UserProfiles

QML_TYPES: tuple[QmlType, ...] = (QmlType(UserProfiles, "UserProfiles", QmlKind.SINGLETON),)


def register_types() -> None:
    register(QML_TYPES)
