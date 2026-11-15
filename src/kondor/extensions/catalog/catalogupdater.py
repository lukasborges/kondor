from enum import Enum, auto
from typing import TYPE_CHECKING

from PySide6.QtCore import QFile, QObject, QTimer, Signal
from PySide6.QtNetwork import QNetworkAccessManager

from kondor.core.settings.settings import Settings
from kondor.extensions.catalog.catalogentry import CatalogEntry, is_newer_version
from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.install.packagedownload import PackageDownload
from kondor.extensions.installresult import InstallResult
from kondor.extensions.package.packagefile import PackageFile
from kondor.extensions.state.extensionaccess import ExtensionAccess, is_silent_update
from kondor.extensions.userscripts.userscriptupdater import UserScriptUpdater, record_update_result

if TYPE_CHECKING:
    from kondor.extensions.catalog.extensioncatalog import ExtensionCatalog

UPDATE_INTERVAL_MILLISECONDS = 24 * 60 * 60 * 1000
FIRST_CHECK_DELAY_MILLISECONDS = 5000
CATALOG_SOURCE = "catalog"


class UpdateDecision(Enum):
    NOT_INSTALLED_FROM_CATALOG = auto()
    UP_TO_DATE = auto()
    NEEDS_REVIEW = auto()
    SILENT = auto()


def has_catalog_install(manager: ExtensionManager) -> bool:
    rows = range(manager.rowCount())
    role = ExtensionManager.Role.SourceRole
    return any(manager.data(manager.index(row, 0), role) == CATALOG_SOURCE for row in rows)


def is_auto_update_on() -> bool:
    return bool(Settings.instance().extensionsAutoUpdate)


def decide_update(entry: CatalogEntry, manager: ExtensionManager) -> UpdateDecision:
    if not manager.isInstalled(entry.id) or manager.source(entry.id) != CATALOG_SOURCE:
        return UpdateDecision.NOT_INSTALLED_FROM_CATALOG
    if not is_newer_version(entry.version, manager.installedVersion(entry.id)):
        return UpdateDecision.UP_TO_DATE
    update = ExtensionAccess(entry.matches, entry.permissions)
    if is_silent_update(update, manager.installed_access(entry.id)):
        return UpdateDecision.SILENT
    return UpdateDecision.NEEDS_REVIEW


class CatalogUpdater(QObject):
    updatesChecked = Signal()

    def __init__(self, catalog: "ExtensionCatalog", network: QNetworkAccessManager) -> None:
        super().__init__(catalog)
        self.catalog = catalog
        self.network = network
        self.user_scripts = UserScriptUpdater(network, self)
        self.updating: list[str] = []
        self.is_setting_connected = False
        self.timer = QTimer(self)
        self.timer.setInterval(UPDATE_INTERVAL_MILLISECONDS)
        self.timer.timeout.connect(self.check_for_updates)

    def react_to_setting_change(self) -> None:
        if not is_auto_update_on():
            self.timer.stop()
            return
        self.timer.start()
        self.check_for_updates()

    def start_auto_update(self) -> None:
        if not self.is_setting_connected:
            self.is_setting_connected = True
            Settings.instance().extensionsAutoUpdateChanged.connect(self.react_to_setting_change)
        if is_auto_update_on():
            self.timer.start()
            QTimer.singleShot(FIRST_CHECK_DELAY_MILLISECONDS, self, self.check_for_updates)

    def check_for_updates(self) -> None:
        if not is_auto_update_on():
            self.timer.stop()
            return
        self.user_scripts.check_all()
        if has_catalog_install(ExtensionManager.instance()):
            self.catalog.refresh()
        else:
            self.updatesChecked.emit()

    def finish_silent_update(self, extension_id: str, path: str, error: str) -> None:
        self.updating.remove(extension_id)
        if not path:
            return record_update_result(extension_id, InstallResult(error=error), "Extension")
        file = PackageFile(path, CATALOG_SOURCE, "", False)
        result = ExtensionManager.instance().update_package(file, extension_id)
        record_update_result(extension_id, result, "Extension")
        QFile.remove(path)
        self.updatesChecked.emit()

    def download_silently(self, entry: CatalogEntry) -> None:
        if not is_auto_update_on() or entry.id in self.updating:
            return
        self.updating.append(entry.id)
        download = PackageDownload(self.network, self)
        download.finished.connect(
            lambda path, error: self.finish_silent_update(entry.id, path, error)
        )
        download.start(entry)

    def apply_update(self, entry: CatalogEntry) -> None:
        manager = ExtensionManager.instance()
        decision = decide_update(entry, manager)
        if decision is UpdateDecision.UP_TO_DATE:
            manager.setUpdateInfo(entry.id, False, False)
        elif decision is UpdateDecision.NEEDS_REVIEW:
            manager.setUpdateInfo(entry.id, True, True)
        elif decision is UpdateDecision.SILENT:
            manager.setUpdateInfo(entry.id, True, False)
            self.download_silently(entry)

    def apply_updates(self, entries: list[CatalogEntry]) -> None:
        for entry in entries:
            self.apply_update(entry)
        self.updatesChecked.emit()
