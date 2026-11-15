from typing import TYPE_CHECKING

from PySide6.QtCore import (
    QT_TRANSLATE_NOOP,
    QCoreApplication,
    QDir,
    QFile,
    QFileInfo,
    QIODevice,
    QUrl,
)
from PySide6.QtNetwork import QNetworkReply, QNetworkRequest

from kondor.extensions.catalog.catalogentry import CONTEXT, CatalogEntry
from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.install.packagedownload import PackageDownload
from kondor.extensions.package.extensionpackage import ExtensionPackage
from kondor.extensions.package.packagefile import PackageFile

if TYPE_CHECKING:
    from kondor.extensions.catalog.extensioncatalog import ExtensionCatalog

DOWNLOAD_FAILED = QT_TRANSLATE_NOOP("ExtensionCatalog", "Could not download “%1”: %2")


def catalog_request(url: QUrl) -> QNetworkRequest:
    request = QNetworkRequest(url)
    request.setAttribute(
        QNetworkRequest.Attribute.RedirectPolicyAttribute,
        QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
    )
    request.setAttribute(
        QNetworkRequest.Attribute.CacheLoadControlAttribute,
        QNetworkRequest.CacheLoadControl.AlwaysNetwork,
    )
    return request


def write_cache(body: bytes, path: str) -> None:
    QDir().mkpath(QFileInfo(path).absolutePath())
    cache = QFile(path)
    if cache.open(QIODevice.OpenModeFlag.WriteOnly | QIODevice.OpenModeFlag.Truncate):
        cache.write(body)


def fail_refresh(catalog: "ExtensionCatalog", message: str) -> None:
    catalog.set_state("ready" if catalog.entries() else "error", message)
    catalog.updatesChecked.emit()


def succeed_refresh(catalog: "ExtensionCatalog", body: bytes) -> None:
    write_cache(body, catalog.cache_file())
    catalog.set_state("ready")
    catalog.updater.apply_updates(catalog.entries())


def handle_refreshed(catalog: "ExtensionCatalog", reply: QNetworkReply) -> None:
    reply.deleteLater()
    catalog.refresh_reply = None
    if reply.error() != QNetworkReply.NetworkError.NoError:
        return fail_refresh(catalog, str(reply.errorString()))
    body = bytes(reply.readAll().data())
    error = catalog.load_catalog(body)
    return fail_refresh(catalog, error) if error else succeed_refresh(catalog, body)


def refresh(catalog: "ExtensionCatalog") -> None:
    if catalog.refresh_reply is not None:
        return
    catalog.set_state("loading")
    reply = catalog.network().get(catalog_request(catalog.catalog_url()))
    catalog.refresh_reply = reply
    reply.finished.connect(lambda: handle_refreshed(catalog, reply))


def finish_install_download(
    catalog: "ExtensionCatalog", name: str, downloaded: tuple[str, str]
) -> None:
    path, error = downloaded
    catalog.set_installing("")
    if not path:
        template = QCoreApplication.translate(CONTEXT, DOWNLOAD_FAILED)
        catalog.set_install_error(template.replace("%1", name).replace("%2", error))
        return
    ExtensionManager.instance().prepare_install(PackageFile(path, "catalog", name, True))


def download_for_install(catalog: "ExtensionCatalog", entry: CatalogEntry) -> None:
    name = ExtensionPackage.localized(entry.json, "name")
    download = PackageDownload(catalog.network(), catalog)
    download.finished.connect(
        lambda path, error: finish_install_download(catalog, name, (path, error))
    )
    download.start(entry)


def install(catalog: "ExtensionCatalog", extension_id: str) -> None:
    entry = catalog.find(extension_id)
    if entry is None or catalog.installingId:
        return
    catalog.set_install_error("")
    catalog.set_installing(extension_id)
    download_for_install(catalog, entry)
