#include "extensions/catalog/catalogupdater.h"

#include <QFile>

#include "core/settings/settings.h"
#include "extensions/catalog/extensioncatalog.h"
#include "extensions/extensionmanager.h"
#include "extensions/install/packagedownload.h"

namespace {

constexpr int kUpdateIntervalMilliseconds = 24 * 60 * 60 * 1000;
constexpr int kFirstCheckDelayMilliseconds = 5000;

bool hasCatalogInstall(const ExtensionManager &manager)
{
    for (int i = 0; i < manager.rowCount(); ++i) {
        if (manager.data(manager.index(i), ExtensionManager::SourceRole).toString()
            == QLatin1String("catalog"))
            return true;
    }
    return false;
}

bool isAutoUpdateOn()
{
    return Settings::instance()->extensionsAutoUpdate();
}

}

UpdateDecision decideUpdate(const CatalogEntry &entry, const ExtensionManager &manager)
{
    if (!manager.isInstalled(entry.id) || manager.source(entry.id) != QLatin1String("catalog"))
        return UpdateDecision::NotInstalledFromCatalog;
    if (!isNewerVersion(entry.version, manager.installedVersion(entry.id)))
        return UpdateDecision::UpToDate;
    const ExtensionAccess update{entry.matches, entry.permissions};
    return ExtensionCatalog::isSilentUpdate(update, manager.installedAccess(entry.id))
        ? UpdateDecision::Silent : UpdateDecision::NeedsReview;
}

CatalogUpdater::CatalogUpdater(ExtensionCatalog *catalog, QNetworkAccessManager &network)
    : QObject(catalog)
    , m_catalog(catalog)
    , m_network(network)
    , m_userScripts(network, this)
{
    m_timer.setInterval(kUpdateIntervalMilliseconds);
    connect(&m_timer, &QTimer::timeout, this, &CatalogUpdater::checkForUpdates);
}

void CatalogUpdater::reactToSettingChange()
{
    if (!isAutoUpdateOn())
        return m_timer.stop();
    m_timer.start();
    checkForUpdates();
}

void CatalogUpdater::startAutoUpdate()
{
    if (!m_isSettingConnected) {
        m_isSettingConnected = true;
        connect(Settings::instance(), &Settings::extensionsAutoUpdateChanged, this,
                &CatalogUpdater::reactToSettingChange);
    }
    if (!isAutoUpdateOn())
        return;
    m_timer.start();
    QTimer::singleShot(kFirstCheckDelayMilliseconds, this, &CatalogUpdater::checkForUpdates);
}

void CatalogUpdater::checkForUpdates()
{
    if (!isAutoUpdateOn())
        return m_timer.stop();
    m_userScripts.checkAll();
    if (hasCatalogInstall(*ExtensionManager::instance()))
        m_catalog->refresh();
    else
        emit updatesChecked();
}

void CatalogUpdater::recordUpdateResult(const QString &id, const InstallResult &result)
{
    ExtensionManager *manager = ExtensionManager::instance();
    if (result.isInstalled)
        manager->setUpdateInfo(id, false, false);
    else if (result.needsReview)
        manager->setUpdateInfo(id, true, true);
    else
        qWarning("Extension %s: update failed: %s", qPrintable(id), qPrintable(result.error));
}

void CatalogUpdater::finishSilentUpdate(const QString &id, const QString &path,
                                        const QString &error)
{
    m_updating.removeAll(id);
    if (path.isEmpty())
        return qWarning("Extension %s: update failed: %s", qPrintable(id), qPrintable(error));
    const PackageFile file{path, QStringLiteral("catalog"), QString(), false};
    recordUpdateResult(id, ExtensionManager::instance()->updatePackage(file, id));
    QFile::remove(path);
    emit updatesChecked();
}

void CatalogUpdater::downloadSilently(const CatalogEntry &entry)
{
    if (!isAutoUpdateOn() || m_updating.contains(entry.id))
        return;
    m_updating.append(entry.id);
    auto *download = new PackageDownload(m_network, this);
    connect(download, &PackageDownload::finished, this,
            [this, id = entry.id](const QString &path, const QString &error) {
                finishSilentUpdate(id, path, error);
            });
    download->start(entry);
}

void CatalogUpdater::applyUpdate(const CatalogEntry &entry)
{
    ExtensionManager *manager = ExtensionManager::instance();
    switch (decideUpdate(entry, *manager)) {
    case UpdateDecision::NotInstalledFromCatalog: break;
    case UpdateDecision::UpToDate: manager->setUpdateInfo(entry.id, false, false); break;
    case UpdateDecision::NeedsReview: manager->setUpdateInfo(entry.id, true, true); break;
    case UpdateDecision::Silent:
        manager->setUpdateInfo(entry.id, true, false);
        downloadSilently(entry);
    }
}

void CatalogUpdater::applyUpdates(const QList<CatalogEntry> &entries)
{
    for (const CatalogEntry &entry : entries)
        applyUpdate(entry);
    emit updatesChecked();
}
