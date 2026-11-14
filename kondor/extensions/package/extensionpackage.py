from typing import Any

from PySide6.QtCore import QDir, QFile, QIODevice, QJsonDocument, QJsonParseError

from kondor.extensions.install import permissiondescription
from kondor.extensions.manifest import localizedmanifest
from kondor.extensions.manifest.jsonvalue import string_at, to_array, to_bool, to_object
from kondor.extensions.manifest.manifestvalidator import (
    ManifestValidator,
    ValidManifest,
    is_valid_id,
)
from kondor.extensions.package import packagearchive
from kondor.extensions.package.contentscript import ExtensionContentScript
from kondor.extensions.package.packagelimits import (
    MAX_PACKAGE_BYTES,
    MAX_PACKAGE_FILES,
    measure_directory,
    package_limit_error,
)
from kondor.extensions.package.packagepath import is_safe_relative_path
from kondor.extensions.state.extensionaccess import ExtensionAccess

__all__ = ["ExtensionContentScript", "ExtensionPackage"]


def invalid_json_error(parse_error: QJsonParseError) -> str:
    no_error = parse_error.error == QJsonParseError.ParseError.NoError
    reason = "not an object" if no_error else parse_error.errorString()
    return f"manifest.json: invalid JSON: {reason}"


def parse_manifest(content: bytes) -> tuple[dict[str, Any] | None, str]:
    parse_error = QJsonParseError()
    document = QJsonDocument.fromJson(content, parse_error)
    no_error = parse_error.error == QJsonParseError.ParseError.NoError
    if no_error and document.isObject():
        return document.object(), ""
    return None, invalid_json_error(parse_error)


def read_manifest(directory: str) -> tuple[dict[str, Any] | None, str]:
    file = QFile(QDir(directory).filePath("manifest.json"))
    if not file.open(QIODevice.OpenModeFlag.ReadOnly):
        return None, "manifest.json: file not found"
    return parse_manifest(bytes(file.readAll().data()))


def unique_entries(scripts: list[ExtensionContentScript], member: str) -> list[str]:
    result: list[str] = []
    for script in scripts:
        result.extend(entry for entry in getattr(script, member) if entry not in result)
    return result


class ExtensionPackage:
    MAX_PACKAGE_BYTES = MAX_PACKAGE_BYTES
    MAX_PACKAGE_FILES = MAX_PACKAGE_FILES

    def __init__(self) -> None:
        self._valid = False
        self._directory = ""
        self._manifest: dict[str, Any] = {}
        self._permissions: list[str] = []
        self._content_scripts: list[ExtensionContentScript] = []
        self._icon_source = ""

    @classmethod
    def load(cls, directory: str) -> tuple["ExtensionPackage", str]:
        package = cls()
        package._directory = QDir(directory).absolutePath()
        return package, package._read_from(directory)

    @staticmethod
    def unpack(zip_path: str, directory: str) -> str:
        return packagearchive.unpack(zip_path, directory)

    @staticmethod
    def is_valid_id(extension_id: str) -> bool:
        return is_valid_id(extension_id)

    @staticmethod
    def localized(source: dict[str, Any], key: str, locale: str = "") -> str:
        return localizedmanifest.localized(source, key, locale)

    @staticmethod
    def permission_entries(
        matches: list[str], permissions: list[str], includes: list[str] | None = None
    ) -> list[dict[str, Any]]:
        return permissiondescription.permission_entries(matches, permissions, includes or [])

    @staticmethod
    def permission_lines(
        matches: list[str], permissions: list[str], includes: list[str] | None = None
    ) -> list[str]:
        return permissiondescription.permission_lines(matches, permissions, includes or [])

    @staticmethod
    def is_subset(candidate: list[str], allowed: list[str]) -> bool:
        return set(candidate) <= set(allowed)

    def is_valid(self) -> bool:
        return self._valid

    def directory(self) -> str:
        return self._directory

    def manifest(self) -> dict[str, Any]:
        return self._manifest

    def id(self) -> str:
        return string_at(self._manifest, "id")

    def version(self) -> str:
        return string_at(self._manifest, "version")

    def author(self) -> str:
        return string_at(self._manifest, "author")

    def homepage(self) -> str:
        return string_at(self._manifest, "homepage")

    def name(self, locale: str = "") -> str:
        return localizedmanifest.localized(self._manifest, "name", locale)

    def description(self, locale: str = "") -> str:
        return localizedmanifest.localized(self._manifest, "description", locale)

    def permissions(self) -> list[str]:
        return list(self._permissions)

    def has_permission(self, permission: str) -> bool:
        return permission in self._permissions

    def content_scripts(self) -> list[ExtensionContentScript]:
        return self._content_scripts

    def all_matches(self) -> list[str]:
        return unique_entries(self._content_scripts, "matches")

    def all_includes(self) -> list[str]:
        return unique_entries(self._content_scripts, "include")

    def access(self) -> ExtensionAccess:
        return ExtensionAccess(self.all_matches(), self._permissions, self.all_includes())

    def user_script(self) -> dict[str, Any]:
        return to_object(self._manifest.get("userScript"))

    def icon_source(self) -> str:
        return self._icon_source

    def settings_schema(self, locale: str = "") -> list[dict[str, Any]]:
        return localizedmanifest.settings_schema(self._manifest, locale)

    def setting_defaults(self) -> dict[str, Any]:
        return localizedmanifest.setting_defaults(self._manifest)

    def has_settings(self) -> bool:
        return bool(to_array(self._manifest.get("settings")))

    def has_action(self) -> bool:
        action = to_object(self._manifest.get("action"))
        return bool(to_array(action.get("items"))) or to_bool(action.get("siteToggle"))

    def action_items(self, locale: str = "") -> list[dict[str, Any]]:
        return localizedmanifest.action_items(self._manifest, locale)

    def action_site_toggle(self) -> bool:
        return to_bool(to_object(self._manifest.get("action")).get("siteToggle"))

    def read_file(self, relative_path: str) -> bytes:
        if not self._valid or not is_safe_relative_path(relative_path):
            return b""
        file = QFile(QDir(self._directory).filePath(relative_path))
        if not file.open(QIODevice.OpenModeFlag.ReadOnly):
            return b""
        return bytes(file.readAll().data())

    def _read_from(self, directory: str) -> str:
        error = package_limit_error(measure_directory(directory))
        if error:
            return error
        manifest, error = read_manifest(directory)
        return self._validate_and_keep(directory, manifest) if manifest is not None else error

    def _validate_and_keep(self, directory: str, manifest: dict[str, Any]) -> str:
        validator = ManifestValidator(directory)
        valid = validator.validate(manifest)
        if valid is None:
            return validator.error()
        self._keep(manifest, valid)
        return ""

    def _keep(self, manifest: dict[str, Any], valid: ValidManifest) -> None:
        self._manifest = manifest
        self._permissions = valid.permissions
        self._content_scripts = valid.content_scripts
        self._icon_source = valid.icon_source
        self._valid = True
