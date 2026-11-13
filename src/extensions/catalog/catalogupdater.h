#pragma once

#include <QNetworkAccessManager>
#include <QObject>
#include <QStringList>
#include <QTimer>

#include "extensions/catalog/catalogentry.h"
#include "extensions/installresult.h"
#include "extensions/userscripts/userscriptupdater.h"

class ExtensionCatalog;
class ExtensionManager;

enum class UpdateDecision {
    NotInstalledFromCatalog,
    UpToDate,
    NeedsReview,
    Silent,
};

UpdateDecision decideUpdate(const CatalogEntry &entry, const ExtensionManager &manager);

class CatalogUpdater : public QObject
{
    Q_OBJECT

public:
    CatalogUpdater(ExtensionCatalog *catalog, QNetworkAccessManager &network);

    void startAutoUpdate();
    void checkForUpdates();
    void applyUpdates(const QList<CatalogEntry> &entries);

signals:
    void updatesChecked();

private:
    void reactToSettingChange();
    void applyUpdate(const CatalogEntry &entry);
    void downloadSilently(const CatalogEntry &entry);
    void finishSilentUpdate(const QString &id, const QString &path, const QString &error);
    void recordUpdateResult(const QString &id, const InstallResult &result);

    ExtensionCatalog *m_catalog;
    QNetworkAccessManager &m_network;
    UserScriptUpdater m_userScripts;
    QTimer m_timer;
    bool m_isSettingConnected = false;
    QStringList m_updating;
};
