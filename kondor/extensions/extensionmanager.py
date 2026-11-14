from typing import ClassVar

from PySide6.QtCore import QUrl, Slot
from PySide6.QtNetwork import QNetworkAccessManager

from kondor.extensions import (
    extensionconfiguration,
    extensioninstall,
    extensionqueries,
)
from kondor.extensions.extensionconfiguration import ConfigurationChange, SiteSwitch
from kondor.extensions.installedextension import JsonMap, find, index_of
from kondor.extensions.manager.extensioninstalls import ExtensionInstalls
from kondor.extensions.state import extensionpins
from kondor.extensions.state.extensionaccess import ExtensionAccess
from kondor.extensions.userscripts.userscriptdownload import UserScriptDownload
from kondor.extensions.userscripts.userscriptpackage import user_script_download_url


class ExtensionManager(ExtensionInstalls):
    _instance: ClassVar["ExtensionManager | None"] = None

    def __init__(self, network: QNetworkAccessManager | None = None) -> None:
        super().__init__()
        self._network = network or QNetworkAccessManager(self)
        self.reload()

    @classmethod
    def instance(cls) -> "ExtensionManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @Slot(str)
    def inspectFile(self, path: str) -> None:
        local = extensioninstall.local_path_of(path)
        if extensioninstall.is_user_script_url(QUrl.fromLocalFile(local)):
            self.inspectUserScript(QUrl.fromLocalFile(local))
        else:
            self.prepare_install(extensioninstall.local_package_file(local))

    def open_package_file(self, path: str) -> None:
        self.inspectFile(path)
        self.manageRequested.emit()

    @Slot(QUrl)
    def inspectUserScript(self, url: QUrl) -> None:
        download = UserScriptDownload(self._network, self)
        download.finished.connect(self.stage_user_script)
        download.start(url)
        self.manageRequested.emit()

    @Slot(str)
    def reviewUserScriptUpdate(self, extension_id: str) -> None:
        user_script = extensioninstall.user_script_of(self._context.entries, extension_id)
        self.inspectUserScript(user_script_download_url(user_script))

    @Slot(QUrl, result=bool)
    def isUserScriptUrl(self, url: QUrl) -> bool:
        return extensioninstall.is_user_script_url(url)

    def user_script_ids(self) -> list[str]:
        return extensioninstall.user_script_ids(self._context.entries)

    def user_script_of(self, extension_id: str) -> JsonMap:
        return extensioninstall.user_script_of(self._context.entries, extension_id)

    @Slot()
    def cancelInstall(self) -> None:
        self.cancel_staged()

    @Slot()
    def confirmInstall(self) -> None:
        self.confirm_staged()

    @Slot(str, result=bool)
    def isInstalled(self, extension_id: str) -> bool:
        return index_of(self._context.entries, extension_id) >= 0

    @Slot(str, result=str)
    def installedVersion(self, extension_id: str) -> str:
        return extensionqueries.installed_version(self._context.entries, extension_id)

    def source(self, extension_id: str) -> str:
        return extensionqueries.installed_source(self._context.entries, extension_id)

    def installed_access(self, extension_id: str) -> ExtensionAccess:
        return extensionqueries.installed_access(self._context.entries, extension_id)

    @Slot(str, bool)
    def setEnabled(self, extension_id: str, enabled: bool) -> None:
        entry = find(self._context.entries, extension_id)
        if entry is None or entry.enabled == enabled:
            return
        entry.enabled = enabled
        self._context.state.set_enabled(extension_id, enabled)
        self._context.state.sync()
        self.row_changed(index_of(self._context.entries, extension_id), [self.Role.EnabledRole])
        self.changed()

    @Slot(str)
    def remove(self, extension_id: str) -> None:
        row = index_of(self._context.entries, extension_id)
        if row < 0:
            return
        self.remove_row(row)
        self.delete_stored_data(extension_id)
        extensionpins.set_pinned(extension_id, False)
        self.extensionRemoved.emit(extension_id)
        self.changed()

    @Slot(str, bool, bool)
    def setUpdateInfo(self, extension_id: str, available: bool, needs_review: bool) -> None:
        entry = find(self._context.entries, extension_id)
        if entry is None:
            return
        if (entry.update_available, entry.update_needs_review) == (available, needs_review):
            return
        entry.update_available, entry.update_needs_review = available, needs_review
        roles = [self.Role.UpdateAvailableRole, self.Role.UpdateNeedsReviewRole]
        self.row_changed(index_of(self._context.entries, extension_id), roles)

    @Slot(str, result="QVariantMap")
    def configurationFor(self, extension_id: str) -> JsonMap:
        return extensionconfiguration.configuration_for(self._context, extension_id)

    @Slot(str, "QVariantMap")
    def applyConfiguration(self, extension_id: str, configuration: JsonMap) -> None:
        entry = find(self._context.entries, extension_id)
        if entry is None:
            return
        change = extensionconfiguration.store_configuration(self._context, entry, configuration)
        row = index_of(self._context.entries, extension_id)
        self.row_changed(row, [self.Role.PrivateAllowedRole])
        self.announce_configuration(extension_id, change)

    def announce_configuration(self, extension_id: str, change: ConfigurationChange) -> None:
        if change.is_any():
            self.changed()
        if change.settings:
            self.settingsChanged.emit(extension_id)

    @Slot(str, result="QVariantMap")
    def settingValues(self, extension_id: str) -> JsonMap:
        return extensionconfiguration.setting_values(self._context, extension_id)

    @Slot(bool, result="QVariantList")
    def actionExtensions(self, is_private: bool) -> list[JsonMap]:
        return extensionqueries.action_extensions(self._context, is_private)

    @Slot(bool, result=bool)
    def hasActionExtensions(self, is_private: bool) -> bool:
        return bool(self.actionExtensions(is_private))

    @Slot(bool, result="QVariantList")
    def pinnedActionExtensions(self, is_private: bool) -> list[JsonMap]:
        return extensionqueries.pinned_action_extensions(self._context, is_private)

    @Slot(str, result=bool)
    def isPinned(self, extension_id: str) -> bool:
        return extensionpins.is_pinned(extension_id)

    @Slot(str, bool)
    def setPinned(self, extension_id: str, pinned: bool) -> None:
        extensionpins.set_pinned(extension_id, pinned)

    @Slot(str, QUrl, result=bool)
    def siteEnabled(self, extension_id: str, url: QUrl) -> bool:
        return extensionconfiguration.site_enabled(self._context, extension_id, url)

    @Slot(str, QUrl, bool)
    def setSiteEnabled(self, extension_id: str, url: QUrl, enabled: bool) -> None:
        switch = SiteSwitch(url, enabled)
        if extensionconfiguration.store_site_enabled(self._context, extension_id, switch):
            self.changed()

    @Slot(QUrl, result=str)
    def originOf(self, url: QUrl) -> str:
        return extensionconfiguration.origin_of(url)

    def check_token(self, extension_id: str, token: str) -> bool:
        return extensionqueries.check_token(self._context.entries, extension_id, token)

    def is_active(self, extension_id: str, private_tab: bool) -> bool:
        return extensionqueries.is_active(self._context.entries, extension_id, private_tab)

    def has_permission(self, extension_id: str, permission: str) -> bool:
        return extensionqueries.has_permission(self._context.entries, extension_id, permission)

    def display_name(self, extension_id: str) -> str:
        return extensionqueries.display_name(self._context, extension_id)
