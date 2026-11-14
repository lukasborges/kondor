from dataclasses import dataclass, field
from typing import Any

from PySide6.QtCore import QRegularExpression

from kondor.extensions.manifest import manifestsections
from kondor.extensions.manifest.jsonvalue import (
    UNDEFINED,
    is_double,
    string_at,
    to_int,
)
from kondor.extensions.manifest.manifesticon import resolve_manifest_icon
from kondor.extensions.manifest.stringlistfield import StringListField, read_string_list
from kondor.extensions.package.contentscript import ExtensionContentScript
from kondor.extensions.scripts.contentscriptreader import ContentScriptReader

REQUIRED_STRING_KEYS = ("id", "name", "version")
OPTIONAL_STRING_KEYS = ("description", "author", "homepage", "license", "icon")
KNOWN_PERMISSIONS = ("tabs", "downloads", "notifications")
ID_PATTERN = "^[a-z0-9][a-z0-9-]{1,47}$"
VERSION_PATTERN = "^\\d+\\.\\d+\\.\\d+$"


def matches(pattern: str, text: str) -> bool:
    return bool(QRegularExpression(pattern).match(text).hasMatch())


def is_valid_id(extension_id: str) -> bool:
    return matches(ID_PATTERN, extension_id)


@dataclass
class ValidManifest:
    permissions: list[str] = field(default_factory=list)
    content_scripts: list[ExtensionContentScript] = field(default_factory=list)
    icon_source: str = ""


class ManifestValidator:
    def __init__(self, directory: str) -> None:
        self._directory = directory
        self._manifest: dict[str, Any] = {}
        self._result = ValidManifest()
        self._error = ""

    def error(self) -> str:
        return self._error

    def validate(self, manifest: dict[str, Any]) -> ValidManifest | None:
        self._manifest = manifest
        self._result = ValidManifest()
        if not self._check_identity() or not self._check_content():
            return None
        return self._result

    def _check_identity(self) -> bool:
        return (
            self._check_api_version()
            and self._check_strings()
            and self._check_id()
            and self._check_version()
        )

    def _check_content(self) -> bool:
        return (
            self._check_permissions()
            and self._check_content_scripts()
            and self._check_settings()
            and self._check_action()
            and self._check_icon()
        )

    def _check_api_version(self) -> bool:
        api = self._manifest.get("kondor", UNDEFINED)
        if api is UNDEFINED:
            return self._fail("kondor: required")
        if not is_double(api) or to_int(api) != 1:
            return self._fail("kondor: unsupported API version (must be 1)")
        return True

    def _check_strings(self) -> bool:
        return all(self._check_required_string(key) for key in REQUIRED_STRING_KEYS) and all(
            self._check_optional_string(key) for key in OPTIONAL_STRING_KEYS
        )

    def _check_required_string(self, key: str) -> bool:
        value = self._manifest.get(key)
        return (isinstance(value, str) and bool(value)) or self._fail(
            f"{key}: required, must be a string"
        )

    def _check_optional_string(self, key: str) -> bool:
        value = self._manifest.get(key, UNDEFINED)
        is_valid = value is UNDEFINED or isinstance(value, str)
        return is_valid or self._fail(f"{key}: must be a string")

    def _check_id(self) -> bool:
        return is_valid_id(self._text("id")) or self._fail(f"id: must match {ID_PATTERN}")

    def _check_version(self) -> bool:
        return matches(VERSION_PATTERN, self._text("version")) or self._fail(
            "version: must be MAJOR.MINOR.PATCH"
        )

    def _check_permissions(self) -> bool:
        permissions, self._error = read_string_list(self._manifest, StringListField("permissions"))
        if permissions is None:
            return False
        self._result.permissions = permissions
        return all(self._check_known_permission(item) for item in permissions)

    def _check_known_permission(self, permission: str) -> bool:
        return permission in KNOWN_PERMISSIONS or self._fail(
            f"permissions: unknown permission: {permission}"
        )

    def _check_content_scripts(self) -> bool:
        scripts = self._manifest.get("contentScripts", UNDEFINED)
        if scripts is not UNDEFINED and not isinstance(scripts, list):
            return self._fail("contentScripts: must be a list")
        entries = scripts if isinstance(scripts, list) else []
        return all(self._check_content_script(value, i) for i, value in enumerate(entries))

    def _check_content_script(self, value: Any, index: int) -> bool:
        where = f"contentScripts[{index}]"
        if not isinstance(value, dict):
            return self._fail(f"{where}: must be an object")
        reader = ContentScriptReader(self._directory, where)
        script = reader.read(value)
        if script is None:
            self._error = reader.error()
            return False
        self._result.content_scripts.append(script)
        return True

    def _check_settings(self) -> bool:
        self._error = manifestsections.settings_error(self._manifest.get("settings", UNDEFINED))
        return not self._error

    def _check_action(self) -> bool:
        self._error = manifestsections.action_error(
            self._manifest.get("action", UNDEFINED), self._manifest.get("settings", UNDEFINED)
        )
        return not self._error

    def _check_icon(self) -> bool:
        icon, self._error = resolve_manifest_icon(self._directory, self._text("icon"))
        if icon is not None:
            self._result.icon_source = icon
        return icon is not None

    def _text(self, key: str) -> str:
        return string_at(self._manifest, key)

    def _fail(self, message: str) -> bool:
        self._error = manifestsections.manifest_error(message)
        return False
