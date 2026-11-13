#include "extensions/userscripts/userscriptupdater.h"

#include <QFile>

#include "extensions/extensionmanager.h"
#include "extensions/userscripts/userscriptdownload.h"
#include "extensions/userscripts/userscriptpackage.h"
#include "extensions/userscripts/userscriptversion.h"

namespace {

QUrl checkUrlOf(const QJsonObject &userScript)
{
    const QString update = userScript.value(QLatin1String("updateURL")).toString();
    const QString download = userScript.value(QLatin1String("downloadURL")).toString();
    const QUrl url(update.isEmpty() ? download : update);
    return isWebUrl(url) ? url : QUrl();
}

}

UserScriptUpdater::UserScriptUpdater(QNetworkAccessManager &network, QObject *parent)
    : QObject(parent)
    , m_network(network)
{
}

void UserScriptUpdater::checkAll()
{
    const QStringList ids = ExtensionManager::instance()->userScriptIds();
    for (const QString &id : ids)
        check(id);
}

void UserScriptUpdater::check(const QString &id)
{
    const QJsonObject userScript = ExtensionManager::instance()->userScriptOf(id);
    const QUrl checkUrl = checkUrlOf(userScript);
    if (checkUrl.isEmpty() || m_checking.contains(id))
        return;
    m_checking.append(id);
    UserScriptDownload *download = newCheckDownload(id);
    if (checkUrl == userScriptDownloadUrl(userScript))
        download->start(checkUrl);
    else
        download->startMetadataOnly(checkUrl);
}

UserScriptDownload *UserScriptUpdater::newCheckDownload(const QString &id)
{
    auto *download = new UserScriptDownload(m_network, this);
    connect(download, &UserScriptDownload::finished, this,
            [this, id](const UserScriptSource &source, const QString &error) {
                m_checking.removeAll(id);
                if (error.isEmpty())
                    handleChecked(id, source);
            });
    return download;
}

void UserScriptUpdater::handleChecked(const QString &id, const UserScriptSource &source)
{
    const QJsonObject userScript = ExtensionManager::instance()->userScriptOf(id);
    const QString installed = userScript.value(QLatin1String("version")).toString();
    if (!isNewerUserScriptVersion(source.metadata.version, installed))
        return;
    const QUrl target = userScriptDownloadUrl(userScript);
    if (source.installUrl == target && source.isComplete())
        install(id, source);
    else
        downloadFull(id, target);
}

void UserScriptUpdater::downloadFull(const QString &id, const QUrl &url)
{
    auto *download = new UserScriptDownload(m_network, this);
    connect(download, &UserScriptDownload::finished, this,
            [this, id](const UserScriptSource &source, const QString &error) {
                if (error.isEmpty())
                    install(id, source);
            });
    download->start(url);
}

void UserScriptUpdater::install(const QString &id, const UserScriptSource &source)
{
    QString error;
    const auto path = writeUserScriptPackage(source, error);
    if (!path)
        return qWarning("User script %s: update failed: %s", qPrintable(id), qPrintable(error));
    const PackageFile file{*path, QStringLiteral("userscript"), QString(), true};
    finishUpdate(id, ExtensionManager::instance()->updatePackage(file, id));
    QFile::remove(*path);
}

void UserScriptUpdater::finishUpdate(const QString &id, const InstallResult &result)
{
    ExtensionManager *manager = ExtensionManager::instance();
    if (result.isInstalled)
        manager->setUpdateInfo(id, false, false);
    else if (result.needsReview)
        manager->setUpdateInfo(id, true, true);
    else
        qWarning("User script %s: update failed: %s", qPrintable(id), qPrintable(result.error));
}
