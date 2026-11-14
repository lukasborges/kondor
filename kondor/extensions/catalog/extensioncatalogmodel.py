from collections.abc import Callable
from enum import IntEnum

from PySide6.QtCore import QByteArray, Qt

from kondor.extensions.catalog.catalogentry import CatalogEntry, is_newer_version
from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.manifest.jsonvalue import to_string
from kondor.extensions.package.extensionpackage import ExtensionPackage

USER_ROLE = Qt.ItemDataRole.UserRole


class Role(IntEnum):
    IdRole = USER_ROLE + 1
    NameRole = USER_ROLE + 2
    DescriptionRole = USER_ROLE + 3
    VersionRole = USER_ROLE + 4
    AuthorRole = USER_ROLE + 5
    IconSourceRole = USER_ROLE + 6
    InstalledRole = USER_ROLE + 7
    UpdateAvailableRole = USER_ROLE + 8


RoleReader = Callable[[CatalogEntry, ExtensionManager], object]


def is_installed_at_least(entry: CatalogEntry, manager: ExtensionManager) -> bool:
    return manager.isInstalled(entry.id) and not is_newer_version(
        entry.version, manager.installedVersion(entry.id)
    )


def has_newer_version(entry: CatalogEntry, manager: ExtensionManager) -> bool:
    return manager.isInstalled(entry.id) and is_newer_version(
        entry.version, manager.installedVersion(entry.id)
    )


ROLE_READERS: dict[int, tuple[bytes, RoleReader]] = {
    Role.IdRole: (b"id", lambda e, m: e.id),
    Role.NameRole: (b"name", lambda e, m: ExtensionPackage.localized(e.json, "name")),
    Role.DescriptionRole: (
        b"description",
        lambda e, m: ExtensionPackage.localized(e.json, "description"),
    ),
    Role.VersionRole: (b"version", lambda e, m: e.version),
    Role.AuthorRole: (b"author", lambda e, m: to_string(e.json.get("author"))),
    Role.IconSourceRole: (b"iconSource", lambda e, m: e.icon_source),
    Role.InstalledRole: (b"installed", is_installed_at_least),
    Role.UpdateAvailableRole: (b"updateAvailable", has_newer_version),
}


def role_value(entry: CatalogEntry, role: int) -> object:
    reader = ROLE_READERS.get(role)
    return None if reader is None else reader[1](entry, ExtensionManager.instance())


def role_names() -> dict[int, QByteArray]:
    return {role: QByteArray(name) for role, (name, _) in ROLE_READERS.items()}
