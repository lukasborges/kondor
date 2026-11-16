from typing import Any

from kondor.profiles.activeprofile import ActiveProfile


def key_of(extension_id: str, name: str) -> str:
    return f"Extensions/{extension_id}/{name}"


def setting_key(extension_id: str, key: str) -> str:
    return key_of(extension_id, "Settings/" + key)


class ExtensionState:
    def __init__(self) -> None:
        self._settings = ActiveProfile.settings()

    def is_enabled(self, extension_id: str) -> bool:
        return bool(self._settings.value(key_of(extension_id, "Enabled"), True, type=bool))

    def set_enabled(self, extension_id: str, is_enabled: bool) -> None:
        self._settings.setValue(key_of(extension_id, "Enabled"), is_enabled)

    def is_private_allowed(self, extension_id: str) -> bool:
        return bool(self._settings.value(key_of(extension_id, "PrivateAllowed"), False, type=bool))

    def set_private_allowed(self, extension_id: str, is_allowed: bool) -> None:
        self._settings.setValue(key_of(extension_id, "PrivateAllowed"), is_allowed)

    def source(self, extension_id: str) -> str:
        return str(self._settings.value(key_of(extension_id, "Source"), "file", type=str))

    def set_source(self, extension_id: str, source: str) -> None:
        self._settings.setValue(key_of(extension_id, "Source"), source)

    def disabled_sites(self, extension_id: str) -> list[str]:
        value = self._settings.value(key_of(extension_id, "DisabledSites"), [], type=list)
        return [str(site) for site in value]

    def set_disabled_sites(self, extension_id: str, sites: list[str]) -> None:
        key = key_of(extension_id, "DisabledSites")
        if sites:
            self._settings.setValue(key, sites)
        else:
            self._settings.remove(key)

    def has_setting(self, extension_id: str, key: str) -> bool:
        return bool(self._settings.contains(setting_key(extension_id, key)))

    def setting(self, extension_id: str, key: str) -> Any:
        return self._settings.value(setting_key(extension_id, key))

    def set_setting(self, extension_id: str, key: str, value: Any) -> None:
        self._settings.setValue(setting_key(extension_id, key), value)

    def remove_extension(self, extension_id: str) -> None:
        self._settings.remove(f"Extensions/{extension_id}")

    def sync(self) -> None:
        self._settings.sync()
