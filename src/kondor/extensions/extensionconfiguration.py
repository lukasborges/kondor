from dataclasses import dataclass
from typing import NamedTuple

from PySide6.QtCore import QUrl

from kondor.extensions.installedextension import ExtensionContext, InstalledExtension, JsonMap, find
from kondor.extensions.state.extensionsettings import sanitize_setting

WEB_SCHEMES = ("http", "https")


@dataclass
class ConfigurationChange:
    settings: bool = False
    privacy: bool = False
    sites: bool = False

    def is_any(self) -> bool:
        return self.settings or self.privacy or self.sites


class SettingValue(NamedTuple):
    setting: JsonMap
    value: object


class SiteSwitch(NamedTuple):
    url: QUrl
    enabled: bool


def key_of(setting: JsonMap) -> str:
    return str(setting.get("key", ""))


def string_list_of(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list | tuple) else []


def map_of(value: object) -> JsonMap:
    return value if isinstance(value, dict) else {}


def stored_values(context: ExtensionContext, extension_id: str, schema: list[JsonMap]) -> JsonMap:
    values: JsonMap = {}
    for setting in schema:
        key = key_of(setting)
        if context.state.has_setting(extension_id, key):
            stored = context.state.setting(extension_id, key)
            values[key] = sanitize_setting(setting, stored)
    return values


def setting_values(context: ExtensionContext, extension_id: str) -> JsonMap:
    entry = find(context.entries, extension_id)
    if entry is None:
        return {}
    schema = entry.package.settings_schema()
    return {**entry.package.setting_defaults(), **stored_values(context, extension_id, schema)}


def settings_with_values(context: ExtensionContext, entry: InstalledExtension) -> list[JsonMap]:
    values = setting_values(context, entry.package.id())
    schema = entry.package.settings_schema(context.locale)
    return [{**item, "value": values.get(key_of(item))} for item in schema]


def configuration_for(context: ExtensionContext, extension_id: str) -> JsonMap:
    entry = find(context.entries, extension_id)
    if entry is None:
        return {}
    return {
        "name": entry.package.name(context.locale),
        "iconSource": entry.package.icon_source(),
        "privateAllowed": entry.private_allowed,
        "disabledSites": context.state.disabled_sites(extension_id),
        "settings": settings_with_values(context, entry),
    }


def store_setting(context: ExtensionContext, extension_id: str, item: SettingValue) -> bool:
    key = key_of(item.setting)
    value = sanitize_setting(item.setting, item.value)
    is_different = bool(value != setting_values(context, extension_id).get(key))
    context.state.set_setting(extension_id, key, value)
    return is_different


def store_settings(context: ExtensionContext, extension_id: str, values: JsonMap) -> bool:
    entry = find(context.entries, extension_id)
    schema = [] if entry is None else entry.package.settings_schema()
    items = [SettingValue(item, values[key_of(item)]) for item in schema if key_of(item) in values]
    return any([store_setting(context, extension_id, item) for item in items])


def store_private_allowed(
    context: ExtensionContext, entry: InstalledExtension, allowed: bool
) -> bool:
    is_different = entry.private_allowed != allowed
    entry.private_allowed = allowed
    context.state.set_private_allowed(entry.package.id(), allowed)
    return is_different


def store_disabled_sites(context: ExtensionContext, extension_id: str, sites: list[str]) -> bool:
    is_different = context.state.disabled_sites(extension_id) != sites
    context.state.set_disabled_sites(extension_id, sites)
    return is_different


def store_configuration(
    context: ExtensionContext, entry: InstalledExtension, configuration: JsonMap
) -> ConfigurationChange:
    extension_id = entry.package.id()
    change = ConfigurationChange()
    change.settings = store_settings(context, extension_id, map_of(configuration.get("settings")))
    allowed = bool(configuration.get("privateAllowed", False))
    change.privacy = store_private_allowed(context, entry, allowed)
    sites = string_list_of(configuration.get("disabledSites"))
    change.sites = store_disabled_sites(context, extension_id, sites)
    context.state.sync()
    return change


def origin_of(url: QUrl) -> str:
    if url.scheme() not in WEB_SCHEMES or not url.host():
        return ""
    origin = f"{url.scheme()}://{url.host().lower()}"
    return f"{origin}:{url.port()}" if url.port() > 0 else origin


def site_enabled(context: ExtensionContext, extension_id: str, url: QUrl) -> bool:
    origin = origin_of(url)
    return not origin or origin not in context.state.disabled_sites(extension_id)


def with_origin(sites: list[str], origin: str, is_enabled: bool) -> list[str]:
    if is_enabled:
        return [site for site in sites if site != origin]
    return [*sites, origin]


def store_site_enabled(context: ExtensionContext, extension_id: str, switch: SiteSwitch) -> bool:
    origin = origin_of(switch.url)
    if not origin or find(context.entries, extension_id) is None:
        return False
    if site_enabled(context, extension_id, switch.url) == switch.enabled:
        return False
    sites = with_origin(context.state.disabled_sites(extension_id), origin, switch.enabled)
    context.state.set_disabled_sites(extension_id, sites)
    context.state.sync()
    return True
