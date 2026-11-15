import os
from typing import ClassVar

from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QByteArray,
    QFile,
    QIODevice,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    QStandardPaths,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply

from kondor.extensions.catalog import extensioncatalogactions, extensioncatalogmodel
from kondor.extensions.catalog.catalogentry import CatalogEntry, parse_catalog
from kondor.extensions.catalog.catalogupdater import CatalogUpdater
from kondor.extensions.catalog.extensioncatalogmodel import Role
from kondor.extensions.extensionmanager import ExtensionManager

DEFAULT_CATALOG_URL = "https://lukasborges.github.io/kondor-extensions/catalog.json"
CONTRIBUTING_URL = "https://github.com/lukasborges/kondor-extensions/blob/main/CONTRIBUTING.md"
CATALOG_URL_VARIABLE = "KONDOR_EXTENSIONS_CATALOG_URL"
CACHE_NAME = "/extensions-catalog.json"
INSTALLED_ROLES = [Role.InstalledRole, Role.UpdateAvailableRole]


class ExtensionCatalog(QAbstractListModel):
    Role = Role
    stateChanged = Signal()
    installingChanged = Signal()
    installErrorChanged = Signal()
    updatesChecked = Signal()

    _instance: ClassVar["ExtensionCatalog | None"] = None

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._network = QNetworkAccessManager(self)
        self.updater = CatalogUpdater(self, self._network)
        self.init_state()
        self.follow_installed_extensions()
        self.show_cached_catalog()
        self.updater.updatesChecked.connect(self.updatesChecked)

    def init_state(self) -> None:
        self._entries: list[CatalogEntry] = []
        self._state = "idle"
        self._error = ""
        self._installing_id = ""
        self._install_error = ""
        self._catalog_url = QUrl()
        self.refresh_reply: QNetworkReply | None = None

    @classmethod
    def instance(cls) -> "ExtensionCatalog":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def follow_installed_extensions(self) -> None:
        manager = ExtensionManager.instance()
        manager.revisionChanged.connect(self.emit_all_changed)
        manager.modelReset.connect(self.emit_all_changed)
        manager.rowsInserted.connect(self.emit_all_changed)
        manager.rowsRemoved.connect(self.emit_all_changed)

    def show_cached_catalog(self) -> None:
        cache = QFile(self.cache_file())
        if cache.open(QIODevice.OpenModeFlag.ReadOnly) and not self.load_catalog(
            bytes(cache.readAll().data())
        ):
            self._state = "ready"

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._entries)

    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = Role.IdRole) -> object:
        if not index.isValid() or not 0 <= index.row() < len(self._entries):
            return None
        return extensioncatalogmodel.role_value(self._entries[index.row()], role)

    def roleNames(self) -> dict[int, QByteArray]:
        return extensioncatalogmodel.role_names()

    def read_state(self) -> str:
        return self._state

    def read_error(self) -> str:
        return self._error

    def read_installing_id(self) -> str:
        return self._installing_id

    def read_install_error(self) -> str:
        return self._install_error

    state = Property(str, read_state, notify=stateChanged)
    errorString = Property(str, read_error, notify=stateChanged)
    installingId = Property(str, read_installing_id, notify=installingChanged)
    installError = Property(str, read_install_error, notify=installErrorChanged)

    def set_state(self, state: str, error: str = "") -> None:
        if (self._state, self._error) == (state, error):
            return
        self._state, self._error = state, error
        self.stateChanged.emit()

    def set_installing(self, extension_id: str) -> None:
        if self._installing_id != extension_id:
            self._installing_id = extension_id
            self.installingChanged.emit()

    def set_install_error(self, error: str) -> None:
        if self._install_error != error:
            self._install_error = error
            self.installErrorChanged.emit()

    def emit_all_changed(self) -> None:
        if self._entries:
            last = self.index(len(self._entries) - 1, 0)
            self.dataChanged.emit(self.index(0, 0), last, INSTALLED_ROLES)

    def catalog_url(self) -> QUrl:
        if self._catalog_url.isValid():
            return self._catalog_url
        override = os.environ.get(CATALOG_URL_VARIABLE, "")
        return QUrl(override or DEFAULT_CATALOG_URL)

    def set_catalog_url(self, url: QUrl) -> None:
        self._catalog_url = url

    @staticmethod
    def cache_file() -> str:
        location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation)
        return str(location) + CACHE_NAME

    def load_catalog(self, json: bytes) -> str:
        entries, error = parse_catalog(json, self.catalog_url())
        if entries is None:
            return error
        self.beginResetModel()
        self._entries = entries
        self.endResetModel()
        return ""

    def entries(self) -> list[CatalogEntry]:
        return self._entries

    def find(self, extension_id: str) -> CatalogEntry | None:
        return next((entry for entry in self._entries if entry.id == extension_id), None)

    def network(self) -> QNetworkAccessManager:
        return self._network

    @Slot()
    def refresh(self) -> None:
        extensioncatalogactions.refresh(self)

    @Slot(str)
    def install(self, extension_id: str) -> None:
        extensioncatalogactions.install(self, extension_id)

    @Slot(result=QUrl)
    def contributingUrl(self) -> QUrl:
        return QUrl(CONTRIBUTING_URL)

    def start_auto_update(self) -> None:
        self.updater.start_auto_update()

    def check_for_updates(self) -> None:
        self.updater.check_for_updates()
