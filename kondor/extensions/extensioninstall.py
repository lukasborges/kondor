from PySide6.QtCore import QFileInfo, QUrl

from kondor.extensions.extensionqueries import installed_version
from kondor.extensions.installedextension import ExtensionContext, InstalledExtension, JsonMap, find
from kondor.extensions.package.extensionpackage import ExtensionPackage
from kondor.extensions.package.packagefile import PackageFile, StagedPackage
from kondor.extensions.userscripts.userscriptdownload import is_fetchable_user_script_url
from kondor.extensions.userscripts.userscriptpackage import (
    UserScriptSource,
    write_user_script_package,
)

USER_SCRIPT_SOURCE = "userscript"
CATALOG_SOURCE = "catalog"
FILE_SOURCE = "file"
USER_SCRIPT_SUFFIX = ".user.js"


def is_user_script_url(url: QUrl) -> bool:
    return is_fetchable_user_script_url(url) and url.path().lower().endswith(USER_SCRIPT_SUFFIX)


def user_script_ids(entries: list[InstalledExtension]) -> list[str]:
    return [e.package.id() for e in entries if e.source == USER_SCRIPT_SOURCE]


def user_script_of(entries: list[InstalledExtension], extension_id: str) -> JsonMap:
    entry = find(entries, extension_id)
    return entry.package.user_script() if entry else {}


def failed_preview(file: PackageFile, error: str) -> JsonMap:
    return {
        "valid": False,
        "fileName": file.label,
        "isUserScript": file.source == USER_SCRIPT_SOURCE,
        "error": error,
    }


def identity_preview(package: ExtensionPackage, locale: str) -> JsonMap:
    return {
        "id": package.id(),
        "name": package.name(locale),
        "version": package.version(),
        "author": package.author(),
        "iconSource": package.icon_source(),
    }


def unsupported_features_of(package: ExtensionPackage) -> list[str]:
    features = package.user_script().get("unsupported", [])
    return [str(feature) for feature in features] if isinstance(features, list) else []


def source_preview(staged: StagedPackage) -> JsonMap:
    return {
        "valid": True,
        "fileName": staged.file.label,
        "fromFile": staged.file.source != CATALOG_SOURCE,
        "isUserScript": staged.file.source == USER_SCRIPT_SOURCE,
    }


def package_preview(package: ExtensionPackage) -> JsonMap:
    entries = ExtensionPackage.permission_entries(
        package.all_matches(), package.permissions(), package.all_includes()
    )
    return {"permissions": entries, "unsupportedFeatures": unsupported_features_of(package)}


def preview_of(context: ExtensionContext, staged: StagedPackage) -> JsonMap:
    package = staged.package
    return {
        **identity_preview(package, context.locale),
        **source_preview(staged),
        **package_preview(package),
        "installedVersion": installed_version(context.entries, package.id()),
    }


def local_path_of(path: str) -> str:
    return QUrl(path).toLocalFile() if path.startswith("file:") else path


def local_package_file(local_path: str) -> PackageFile:
    return PackageFile(local_path, FILE_SOURCE, QFileInfo(local_path).fileName(), False)


def user_script_package_file(source: UserScriptSource, error: str) -> tuple[PackageFile, str]:
    label = source.install_url.fileName()
    file = PackageFile("", USER_SCRIPT_SOURCE, label, False)
    if error:
        return file, error
    path, package_error = write_user_script_package(source)
    if path is None:
        return file, package_error
    return PackageFile(path, USER_SCRIPT_SOURCE, label, True), ""
