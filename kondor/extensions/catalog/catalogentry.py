from dataclasses import dataclass, field
from typing import Any

from PySide6.QtCore import QCoreApplication, QJsonDocument, QJsonParseError, QUrl, QVersionNumber

from kondor.extensions.manifest.jsonvalue import is_double, to_array, to_object, to_string
from kondor.extensions.package.extensionpackage import ExtensionPackage

CONTEXT = "ExtensionCatalog"
DEFAULT_ICON = "preferences-plugin"
NOT_JSON = "The catalog is not valid JSON"
UNSUPPORTED_FORMAT = "The catalog has an unsupported format"
SUPPORTED_FORMAT_VERSION = 1


@dataclass
class CatalogEntry:
    id: str = ""
    json: dict[str, Any] = field(default_factory=dict)
    version: str = ""
    matches: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    package: QUrl = field(default_factory=QUrl)
    sha256: str = ""
    size: int = 0
    icon_source: str = ""


def string_list(value: Any) -> list[str]:
    return [item for item in to_array(value) if isinstance(item, str)]


def size_of(value: Any) -> int:
    return int(value) if is_double(value) else 0


def identity_of(source: dict[str, Any]) -> CatalogEntry:
    return CatalogEntry(
        id=to_string(source.get("id")),
        json=source,
        version=to_string(source.get("version")),
        matches=string_list(source.get("matches")),
        permissions=string_list(source.get("permissions")),
        sha256=to_string(source.get("sha256")).lower(),
        size=size_of(source.get("size")),
    )


def icon_source_of(icon: str, catalog_url: QUrl) -> str:
    if not icon:
        return DEFAULT_ICON
    if "/" in icon or "." in icon:
        return str(catalog_url.resolved(QUrl(icon)).toString())
    return icon


def parse_catalog_entry(source: dict[str, Any], catalog_url: QUrl) -> CatalogEntry | None:
    package = to_string(source.get("package"))
    entry = identity_of(source)
    if not ExtensionPackage.is_valid_id(entry.id) or not entry.version or not package:
        return None
    entry.package = catalog_url.resolved(QUrl(package))
    entry.icon_source = icon_source_of(to_string(source.get("icon")), catalog_url)
    return entry


def has_supported_format(root: dict[str, Any]) -> bool:
    version = root.get("version")
    is_supported = isinstance(version, int | float) and version == SUPPORTED_FORMAT_VERSION
    return is_supported and isinstance(root.get("extensions"), list)


def entries_of(items: list[Any], catalog_url: QUrl) -> list[CatalogEntry]:
    parsed = (parse_catalog_entry(to_object(item), catalog_url) for item in items)
    return [entry for entry in parsed if entry is not None]


def parse_catalog(json: bytes, catalog_url: QUrl) -> tuple[list[CatalogEntry] | None, str]:
    error = QJsonParseError()
    document = QJsonDocument.fromJson(json, error)
    if error.error != QJsonParseError.ParseError.NoError or not document.isObject():
        return None, QCoreApplication.translate(CONTEXT, NOT_JSON)
    root = document.object()
    if not has_supported_format(root):
        return None, QCoreApplication.translate(CONTEXT, UNSUPPORTED_FORMAT)
    return entries_of(root["extensions"], catalog_url), ""


def is_newer_version(candidate: str, installed: str) -> bool:
    return bool(version_of(candidate) > version_of(installed))


def version_of(text: str) -> QVersionNumber:
    parsed = QVersionNumber.fromString(text)
    return parsed[0] if isinstance(parsed, tuple) else parsed
