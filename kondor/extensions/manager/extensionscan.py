from PySide6.QtCore import QDir, QFileInfo, QUuid, qWarning

from kondor.extensions.installedextension import ExtensionContext, InstalledExtension
from kondor.extensions.package.extensionpackage import ExtensionPackage

DIRECTORY_FILTER = QDir.Filter.Dirs | QDir.Filter.NoDotAndDotDot | QDir.Filter.Hidden
DIFFERENT_ID = "directory name differs from id"


def is_interrupted_install(info: QFileInfo) -> bool:
    name = str(info.fileName())
    return name.endswith((".new", ".old")) or name.startswith(".")


def make_entry(context: ExtensionContext, package: ExtensionPackage) -> InstalledExtension:
    extension_id = package.id()
    return InstalledExtension(
        package=package,
        enabled=context.state.is_enabled(extension_id),
        private_allowed=context.state.is_private_allowed(extension_id),
        source=context.state.source(extension_id),
        token=QUuid.createUuid().toString(QUuid.StringFormat.WithoutBraces),
    )


def load_installed(context: ExtensionContext, info: QFileInfo) -> InstalledExtension | None:
    package, error = ExtensionPackage.load(info.absoluteFilePath())
    if package.is_valid() and package.id() == info.fileName():
        return make_entry(context, package)
    qWarning(f"Extension {info.fileName()} ignored: {error or DIFFERENT_ID}")
    return None


def installed_in(context: ExtensionContext, info: QFileInfo) -> InstalledExtension | None:
    if not is_interrupted_install(info):
        return load_installed(context, info)
    QDir(info.absoluteFilePath()).removeRecursively()
    return None


def scan_installed(context: ExtensionContext, directory: str) -> list[InstalledExtension]:
    infos = QDir(directory).entryInfoList(DIRECTORY_FILTER, QDir.SortFlag.Name)
    entries = [installed_in(context, info) for info in infos]
    return [entry for entry in entries if entry is not None]
