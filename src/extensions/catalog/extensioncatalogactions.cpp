#include "extensions/catalog/extensioncatalog.h"

#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QNetworkReply>
#include <QNetworkRequest>

#include "extensions/catalog/catalogupdater.h"
#include "extensions/extensionmanager.h"
#include "extensions/install/packagedownload.h"

namespace {

QNetworkRequest catalogRequest(const QUrl &url)
{
    QNetworkRequest request(url);
    request.setAttribute(QNetworkRequest::RedirectPolicyAttribute,
                         QNetworkRequest::NoLessSafeRedirectPolicy);
    request.setAttribute(QNetworkRequest::CacheLoadControlAttribute, QNetworkRequest::AlwaysNetwork);
    return request;
}

void writeCache(const QByteArray &body)
{
    const QString path = ExtensionCatalog::cacheFile();
    QDir().mkpath(QFileInfo(path).absolutePath());
    QFile cache(path);
    if (cache.open(QIODevice::WriteOnly | QIODevice::Truncate))
        cache.write(body);
}

}

void ExtensionCatalog::failRefresh(const QString &message)
{
    setState(m_entries.isEmpty() ? QStringLiteral("error") : QStringLiteral("ready"), message);
    emit updatesChecked();
}

void ExtensionCatalog::succeedRefresh(const QByteArray &body)
{
    writeCache(body);
    setState(QStringLiteral("ready"));
    m_updater->applyUpdates(m_entries);
}

void ExtensionCatalog::handleRefreshed(QNetworkReply *reply)
{
    reply->deleteLater();
    if (m_refreshReply == reply)
        m_refreshReply = nullptr;
    if (reply->error() != QNetworkReply::NoError)
        return failRefresh(reply->errorString());
    const QByteArray body = reply->readAll();
    QString error;
    if (!loadCatalog(body, &error))
        return failRefresh(error);
    succeedRefresh(body);
}

void ExtensionCatalog::refresh()
{
    if (m_refreshReply)
        return;
    setState(QStringLiteral("loading"));
    QNetworkReply *reply = m_network.get(catalogRequest(catalogUrl()));
    m_refreshReply = reply;
    connect(reply, &QNetworkReply::finished, this, [this, reply]() { handleRefreshed(reply); });
}

void ExtensionCatalog::finishInstallDownload(const QString &name, const QString &path,
                                             const QString &error)
{
    setInstalling(QString());
    if (path.isEmpty())
        return setInstallError(tr("Could not download “%1”: %2").arg(name, error));
    ExtensionManager::instance()->prepareInstall({path, QStringLiteral("catalog"), name, true});
}

void ExtensionCatalog::downloadForInstall(const CatalogEntry &entry)
{
    const QString name = ExtensionPackage::localized(entry.json, QStringLiteral("name"));
    auto *download = new PackageDownload(m_network, this);
    connect(download, &PackageDownload::finished, this,
            [this, name](const QString &path, const QString &error) {
                finishInstallDownload(name, path, error);
            });
    download->start(entry);
}

void ExtensionCatalog::install(const QString &id)
{
    const CatalogEntry *entry = find(id);
    if (!entry || !m_installingId.isEmpty())
        return;
    setInstallError(QString());
    setInstalling(id);
    downloadForInstall(*entry);
}

void ExtensionCatalog::startAutoUpdate()
{
    m_updater->startAutoUpdate();
}

void ExtensionCatalog::checkForUpdates()
{
    m_updater->checkForUpdates();
}
