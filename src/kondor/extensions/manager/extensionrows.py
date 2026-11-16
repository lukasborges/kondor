from collections.abc import Sequence

from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QByteArray,
    QDir,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Signal,
)
from PySide6.QtWebEngineCore import QWebEngineScript
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.extensions import extensionmodel, extensionscripts
from kondor.extensions.extensionmodel import Role
from kondor.extensions.install.extensioninstaller import ExtensionInstaller
from kondor.extensions.installedextension import (
    ExtensionContext,
    InstalledExtension,
    JsonMap,
    find,
    index_of,
)
from kondor.extensions.manager.extensionscan import make_entry, scan_installed
from kondor.extensions.package.extensionpackage import ExtensionPackage
from kondor.extensions.scripts.profilescripts import ProfileScripts
from kondor.extensions.state.extensionstate import ExtensionState
from kondor.extensions.state.extensionstorage import remove_extension as remove_storage
from kondor.profiles.activeprofile import ActiveProfile


class ExtensionRows(QAbstractListModel):
    Role = Role
    countChanged = Signal()
    revisionChanged = Signal()
    pendingInstallChanged = Signal()
    settingsChanged = Signal(str)
    manageRequested = Signal()
    extensionRemoved = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._context = ExtensionContext(ExtensionState())
        self._revision = 0
        self._pending_preview: JsonMap = {}
        self._scripts = ProfileScripts(self)

    @staticmethod
    def extensions_directory() -> str:
        return f"{ActiveProfile.data_directory()}/extensions"

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._context.entries)

    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = Role.IdRole) -> object:
        if not index.isValid() or not 0 <= index.row() < len(self._context.entries):
            return None
        return extensionmodel.role_value(
            self._context.entries[index.row()], role, self._context.locale
        )

    def roleNames(self) -> dict[int, QByteArray]:
        return extensionmodel.role_names()

    def entry_count(self) -> int:
        return len(self._context.entries)

    def revision_number(self) -> int:
        return self._revision

    def pending_preview(self) -> JsonMap:
        return self._pending_preview

    count = Property(int, entry_count, notify=countChanged)
    revision = Property(int, revision_number, notify=revisionChanged)
    pendingInstall = Property("QVariantMap", pending_preview, notify=pendingInstallChanged)

    def set_locale(self, locale: str) -> None:
        self._context.locale = locale

    def installer(self) -> ExtensionInstaller:
        return ExtensionInstaller(self.extensions_directory())

    def make_entry(self, package: ExtensionPackage) -> InstalledExtension:
        return make_entry(self._context, package)

    def reload(self) -> None:
        self.beginResetModel()
        self._context.entries = scan_installed(self._context, self.extensions_directory())
        self.endResetModel()
        self.countChanged.emit()
        self.changed()

    def changed(self) -> None:
        self._revision += 1
        self.revisionChanged.emit()
        self.rebuild_scripts()

    def rebuild_scripts(self) -> None:
        self._scripts.rebuild_once_after_several_changes()

    def register_profile(self, profile: QQuickWebEngineProfile | None) -> None:
        self._scripts.register_profile(profile)

    def scripts_for(self, private_profile: bool) -> list[QWebEngineScript]:
        return extensionscripts.scripts_for(self._context, private_profile)

    def script_source(self, extension_id: str, index: int, private_profile: bool) -> str:
        entry = find(self._context.entries, extension_id)
        target = extensionscripts.source_target(entry, index, private_profile)
        return extensionscripts.script_source(self._context, target)

    def row_changed(self, row: int, roles: Sequence[int]) -> None:
        self.dataChanged.emit(self.index(row), self.index(row), roles)

    def append_row(self, entry: InstalledExtension) -> None:
        count = len(self._context.entries)
        self.beginInsertRows(QModelIndex(), count, count)
        self._context.entries.append(entry)
        self.endInsertRows()
        self.countChanged.emit()

    def replace_row(self, row: int, entry: InstalledExtension) -> None:
        self._context.entries[row] = entry
        self.row_changed(row, [])
        self.settingsChanged.emit(entry.package.id())

    def put_entry(self, entry: InstalledExtension) -> None:
        row = index_of(self._context.entries, entry.package.id())
        if row >= 0:
            self.replace_row(row, entry)
        else:
            self.append_row(entry)

    def remove_row(self, row: int) -> None:
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._context.entries[row]
        self.endRemoveRows()
        self.countChanged.emit()

    def delete_stored_data(self, extension_id: str) -> None:
        QDir(f"{self.extensions_directory()}/{extension_id}").removeRecursively()
        self._context.state.remove_extension(extension_id)
        self._context.state.sync()
        remove_storage(extension_id)
