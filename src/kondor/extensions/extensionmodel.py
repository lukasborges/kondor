from collections.abc import Callable
from enum import IntEnum

from PySide6.QtCore import QByteArray, Qt

from kondor.extensions.installedextension import InstalledExtension
from kondor.extensions.package.extensionpackage import ExtensionPackage

USER_ROLE = Qt.ItemDataRole.UserRole


class Role(IntEnum):
    IdRole = USER_ROLE + 1
    NameRole = USER_ROLE + 2
    DescriptionRole = USER_ROLE + 3
    VersionRole = USER_ROLE + 4
    AuthorRole = USER_ROLE + 5
    HomepageRole = USER_ROLE + 6
    IconSourceRole = USER_ROLE + 7
    EnabledRole = USER_ROLE + 8
    PrivateAllowedRole = USER_ROLE + 9
    PermissionsRole = USER_ROLE + 10
    HasSettingsRole = USER_ROLE + 11
    HasActionRole = USER_ROLE + 12
    SourceRole = USER_ROLE + 13
    UpdateAvailableRole = USER_ROLE + 14
    UpdateNeedsReviewRole = USER_ROLE + 15


RoleReader = Callable[[InstalledExtension, str], object]


def permission_lines_of(package: ExtensionPackage) -> list[str]:
    return ExtensionPackage.permission_lines(
        package.all_matches(), package.permissions(), package.all_includes()
    )


ROLE_READERS: dict[int, tuple[bytes, RoleReader]] = {
    Role.IdRole: (b"id", lambda e, locale: e.package.id()),
    Role.NameRole: (b"name", lambda e, locale: e.package.name(locale)),
    Role.DescriptionRole: (b"description", lambda e, locale: e.package.description(locale)),
    Role.VersionRole: (b"version", lambda e, locale: e.package.version()),
    Role.AuthorRole: (b"author", lambda e, locale: e.package.author()),
    Role.HomepageRole: (b"homepage", lambda e, locale: e.package.homepage()),
    Role.IconSourceRole: (b"iconSource", lambda e, locale: e.package.icon_source()),
    Role.EnabledRole: (b"enabled", lambda e, locale: e.enabled),
    Role.PrivateAllowedRole: (b"privateAllowed", lambda e, locale: e.private_allowed),
    Role.PermissionsRole: (b"permissions", lambda e, locale: permission_lines_of(e.package)),
    Role.HasSettingsRole: (b"hasSettings", lambda e, locale: e.package.has_settings()),
    Role.HasActionRole: (b"hasAction", lambda e, locale: e.package.has_action()),
    Role.SourceRole: (b"source", lambda e, locale: e.source),
    Role.UpdateAvailableRole: (b"updateAvailable", lambda e, locale: e.update_available),
    Role.UpdateNeedsReviewRole: (b"updateNeedsReview", lambda e, locale: e.update_needs_review),
}


def role_value(entry: InstalledExtension, role: int, locale: str) -> object:
    reader = ROLE_READERS.get(role)
    return None if reader is None else reader[1](entry, locale)


def role_names() -> dict[int, QByteArray]:
    return {role: QByteArray(name) for role, (name, _) in ROLE_READERS.items()}
