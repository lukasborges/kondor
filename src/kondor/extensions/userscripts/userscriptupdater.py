from typing import Any

from PySide6.QtCore import QFile, QObject, QUrl, qWarning
from PySide6.QtNetwork import QNetworkAccessManager

from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.installresult import InstallResult
from kondor.extensions.manifest.jsonvalue import string_at
from kondor.extensions.package.packagefile import PackageFile
from kondor.extensions.userscripts.userscriptdownload import UserScriptDownload, is_web_url
from kondor.extensions.userscripts.userscriptpackage import (
    UserScriptSource,
    user_script_download_url,
    write_user_script_package,
)
from kondor.extensions.userscripts.userscriptversion import is_newer_user_script_version


def check_url_of(user_script: dict[str, Any]) -> QUrl:
    update = string_at(user_script, "updateURL")
    url = QUrl(update or string_at(user_script, "downloadURL"))
    return url if is_web_url(url) else QUrl()


def record_update_result(extension_id: str, result: InstallResult, prefix: str) -> None:
    manager = ExtensionManager.instance()
    if result.is_installed:
        manager.setUpdateInfo(extension_id, False, False)
    elif result.needs_review:
        manager.setUpdateInfo(extension_id, True, True)
    else:
        qWarning(f"{prefix} {extension_id}: update failed: {result.error}")


class UserScriptUpdater(QObject):
    def __init__(self, network: QNetworkAccessManager, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.network = network
        self.checking: list[str] = []

    def check_all(self) -> None:
        for extension_id in ExtensionManager.instance().user_script_ids():
            self.check(extension_id)

    def check(self, extension_id: str) -> None:
        user_script = ExtensionManager.instance().user_script_of(extension_id)
        check_url = check_url_of(user_script)
        if check_url.isEmpty() or extension_id in self.checking:
            return
        self.checking.append(extension_id)
        download = self.new_check_download(extension_id)
        if check_url == user_script_download_url(user_script):
            download.start(check_url)
        else:
            download.start_metadata_only(check_url)

    def new_check_download(self, extension_id: str) -> UserScriptDownload:
        download = UserScriptDownload(self.network, self)
        download.finished.connect(
            lambda source, error: self.finish_check(extension_id, source, error)
        )
        return download

    def finish_check(self, extension_id: str, source: UserScriptSource, error: str) -> None:
        self.checking.remove(extension_id)
        if not error:
            self.handle_checked(extension_id, source)

    def handle_checked(self, extension_id: str, source: UserScriptSource) -> None:
        user_script = ExtensionManager.instance().user_script_of(extension_id)
        installed = string_at(user_script, "version")
        if not is_newer_user_script_version(source.metadata.version, installed):
            return
        target = user_script_download_url(user_script)
        if source.install_url == target and source.is_complete():
            self.install(extension_id, source)
        else:
            self.download_full(extension_id, target)

    def download_full(self, extension_id: str, url: QUrl) -> None:
        download = UserScriptDownload(self.network, self)
        download.finished.connect(
            lambda source, error: self.finish_full(extension_id, source, error)
        )
        download.start(url)

    def finish_full(self, extension_id: str, source: UserScriptSource, error: str) -> None:
        if not error:
            self.install(extension_id, source)

    def install(self, extension_id: str, source: UserScriptSource) -> None:
        path, error = write_user_script_package(source)
        if path is None:
            qWarning(f"User script {extension_id}: update failed: {error}")
            return
        file = PackageFile(path, "userscript", "", True)
        result = ExtensionManager.instance().update_package(file, extension_id)
        record_update_result(extension_id, result, "User script")
        QFile.remove(path)
