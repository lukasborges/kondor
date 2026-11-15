from functools import cmp_to_key

from PySide6.QtCore import QCollator

from kondor.extensions.action.actionitemdisplay import for_display
from kondor.extensions.extensionconfiguration import setting_values
from kondor.extensions.installedextension import ExtensionContext, InstalledExtension, JsonMap, find
from kondor.extensions.state.extensionaccess import ExtensionAccess
from kondor.extensions.state.extensionpins import only_pinned


def has_visible_action(entry: InstalledExtension, is_private: bool) -> bool:
    return (
        entry.enabled and entry.package.has_action() and (not is_private or entry.private_allowed)
    )


def action_entry(context: ExtensionContext, entry: InstalledExtension, is_private: bool) -> JsonMap:
    package = entry.package
    values = setting_values(context, package.id())
    items = for_display(package.action_items(context.locale), values)
    return {
        "id": package.id(),
        "name": package.name(context.locale),
        "iconSource": package.icon_source(),
        "siteToggle": package.action_site_toggle() and not is_private,
        "items": items,
    }


def sorted_by_name(entries: list[JsonMap]) -> list[JsonMap]:
    collator = QCollator()

    def compare_names(first: JsonMap, second: JsonMap) -> int:
        return int(collator.compare(first["name"], second["name"]))

    return sorted(entries, key=cmp_to_key(compare_names))


def action_extensions(context: ExtensionContext, is_private: bool) -> list[JsonMap]:
    visible = [e for e in context.entries if has_visible_action(e, is_private)]
    return sorted_by_name([action_entry(context, entry, is_private) for entry in visible])


def pinned_action_extensions(context: ExtensionContext, is_private: bool) -> list[JsonMap]:
    return only_pinned(action_extensions(context, is_private))


def installed_version(entries: list[InstalledExtension], extension_id: str) -> str:
    entry = find(entries, extension_id)
    return entry.package.version() if entry else ""


def installed_source(entries: list[InstalledExtension], extension_id: str) -> str:
    entry = find(entries, extension_id)
    return entry.source if entry else ""


def installed_access(entries: list[InstalledExtension], extension_id: str) -> ExtensionAccess:
    entry = find(entries, extension_id)
    return entry.package.access() if entry else ExtensionAccess([], [], [])


def check_token(entries: list[InstalledExtension], extension_id: str, token: str) -> bool:
    entry = find(entries, extension_id)
    return entry is not None and bool(token) and entry.token == token


def is_active(entries: list[InstalledExtension], extension_id: str, is_private: bool) -> bool:
    entry = find(entries, extension_id)
    return entry is not None and entry.enabled and (not is_private or entry.private_allowed)


def has_permission(entries: list[InstalledExtension], extension_id: str, permission: str) -> bool:
    entry = find(entries, extension_id)
    return entry is not None and entry.package.has_permission(permission)


def display_name(context: ExtensionContext, extension_id: str) -> str:
    entry = find(context.entries, extension_id)
    return entry.package.name(context.locale) if entry else extension_id
