#include "extensions/extensionmanager.h"

#include "extensions/catalog/extensioncatalog.h"
#include "extensions/userscripts/userscriptdownload.h"
#include "extensions/userscripts/userscriptpackage.h"

bool ExtensionManager::isUserScriptUrl(const QUrl &url)
{
    return isFetchableUserScriptUrl(url)
        && url.path().endsWith(QLatin1String(".user.js"), Qt::CaseInsensitive);
}

QStringList ExtensionManager::userScriptIds() const
{
    QStringList ids;
    for (const InstalledExtension &entry : m_entries) {
        if (entry.source == QLatin1String("userscript"))
            ids.append(entry.package.id());
    }
    return ids;
}

QJsonObject ExtensionManager::userScriptOf(const QString &id) const
{
    const InstalledExtension *entry = find(id);
    return entry ? entry->package.userScript() : QJsonObject();
}

void ExtensionManager::inspectUserScript(const QUrl &url)
{
    auto *download = new UserScriptDownload(ExtensionCatalog::instance()->network(), this);
    connect(download, &UserScriptDownload::finished, this, &ExtensionManager::stageUserScript);
    download->start(url);
    emit manageRequested();
}

void ExtensionManager::reviewUserScriptUpdate(const QString &id)
{
    inspectUserScript(userScriptDownloadUrl(userScriptOf(id)));
}

void ExtensionManager::stageUserScript(const UserScriptSource &source, const QString &error)
{
    const PackageFile file{QString(), QStringLiteral("userscript"), source.installUrl.fileName(), false};
    if (!error.isEmpty())
        return refusePackage(file, error);
    QString packageError;
    const auto path = writeUserScriptPackage(source, packageError);
    if (!path)
        return refusePackage(file, packageError);
    prepareInstall({*path, file.source, file.label, true});
}
