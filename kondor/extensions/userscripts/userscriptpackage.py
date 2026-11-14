import hashlib
import zipfile
from dataclasses import dataclass, field
from typing import Any

from PySide6.QtCore import (
    QCoreApplication,
    QDir,
    QFile,
    QIODevice,
    QJsonDocument,
    QTemporaryFile,
    QUrl,
)

from kondor.extensions.userscripts.userscriptmetadata import UserScriptMetadata
from kondor.extensions.userscripts.userscriptversion import normalized_user_script_version

GM_RESOURCE = ":/scripts/usergm.js"
TEMPORARY_TEMPLATE = "/kondor-userscript-XXXXXX.kondorext"
OPTIONAL_FIELDS = ("description", "author", "homepage", "license")


@dataclass
class UserScriptSource:
    metadata: UserScriptMetadata = field(default_factory=UserScriptMetadata)
    script: bytes = b""
    required_scripts: list[bytes] = field(default_factory=list)
    install_url: QUrl = field(default_factory=QUrl)

    def is_complete(self) -> bool:
        return len(self.required_scripts) == len(self.metadata.required_urls)


def to_json(value: dict[str, Any], format: QJsonDocument.JsonFormat) -> bytes:
    return bytes(QJsonDocument(value).toJson(format).data())


def user_script_id(metadata: UserScriptMetadata) -> str:
    identity = f"{metadata.namespace_name}\n{metadata.name}".encode()
    return "user-" + hashlib.sha256(identity).hexdigest()[:16]


def script_files(source: UserScriptSource) -> list[str]:
    required = [f"require-{n}.js" for n in range(1, len(source.required_scripts) + 1)]
    return ["gm.js", *required, "script.js"]


def content_script_of(source: UserScriptSource) -> dict[str, Any]:
    metadata = source.metadata
    return {
        "matches": metadata.matches,
        "include": metadata.includes,
        "exclude": metadata.excludes,
        "js": script_files(source),
        "runAt": metadata.run_at,
        "allFrames": metadata.all_frames,
    }


def user_script_section(source: UserScriptSource) -> dict[str, Any]:
    metadata = source.metadata
    return {
        "version": metadata.version,
        "namespace": metadata.namespace_name,
        "installURL": source.install_url.toString(),
        "updateURL": metadata.update_url,
        "downloadURL": metadata.download_url,
        "unsupported": metadata.unsupported_features(),
    }


def identity_of(metadata: UserScriptMetadata) -> dict[str, Any]:
    return {
        "kondor": 1,
        "id": user_script_id(metadata),
        "name": metadata.name,
        "version": normalized_user_script_version(metadata.version),
        "icon": "text-x-javascript",
        "permissions": ["notifications"] if metadata.wants_notifications() else [],
    }


def user_script_manifest(source: UserScriptSource) -> dict[str, Any]:
    manifest = identity_of(source.metadata)
    manifest["contentScripts"] = [content_script_of(source)]
    manifest["userScript"] = user_script_section(source)
    for key in OPTIONAL_FIELDS:
        if getattr(source.metadata, key):
            manifest[key] = getattr(source.metadata, key)
    return manifest


def user_script_download_url(user_script: dict[str, Any]) -> QUrl:
    download = user_script.get("downloadURL")
    install = user_script.get("installURL")
    chosen = download if isinstance(download, str) and download else install
    return QUrl(chosen if isinstance(chosen, str) else "")


def gm_declaration(metadata: UserScriptMetadata) -> str:
    script = {
        "name": metadata.name,
        "namespace": metadata.namespace_name,
        "version": metadata.version,
        "description": metadata.description,
        "kondorVersion": QCoreApplication.applicationVersion(),
    }
    compact = to_json(script, QJsonDocument.JsonFormat.Compact).decode()
    return f"const __userScript = {compact};\n"


def gm_source(metadata: UserScriptMetadata) -> bytes:
    file = QFile(GM_RESOURCE)
    if not file.open(QIODevice.OpenModeFlag.ReadOnly):
        return b""
    return gm_declaration(metadata).encode() + bytes(file.readAll().data())


def package_entries(source: UserScriptSource) -> dict[str, bytes]:
    manifest = to_json(user_script_manifest(source), QJsonDocument.JsonFormat.Indented)
    required = {f"require-{n}.js": body for n, body in enumerate(source.required_scripts, 1)}
    gm = {"gm.js": gm_source(source.metadata)}
    return {"manifest.json": manifest, **gm, **required, "script.js": source.script}


def write_entries(archive: zipfile.ZipFile, source: UserScriptSource) -> None:
    for name, body in package_entries(source).items():
        archive.writestr(name, body)


def write_zip(path: str, source: UserScriptSource) -> bool:
    try:
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            write_entries(archive, source)
    except OSError:
        return False
    return True


def write_user_script_package(source: UserScriptSource) -> tuple[str | None, str]:
    file = QTemporaryFile(QDir.tempPath() + TEMPORARY_TEMPLATE)
    file.setAutoRemove(False)
    if file.open():
        file.close()
        if write_zip(file.fileName(), source):
            return file.fileName(), ""
        QFile.remove(file.fileName())
    return None, QCoreApplication.translate("UserScript", "Cannot create the package")
