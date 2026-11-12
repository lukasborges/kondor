#pragma once

#include "adblock/filterengine.h"

#include <QDateTime>
#include <QFutureWatcher>
#include <QHash>
#include <QList>
#include <QObject>
#include <QSet>
#include <QString>
#include <QtQmlIntegration/qqmlintegration.h>

#include <memory>

class AdBlockInterceptor;
class QNetworkAccessManager;
class QNetworkReply;
class QQmlEngine;
class QJSEngine;
class QQuickWebEngineProfile;

// QML singleton `AdBlockManager`: owns the filter lists (EasyList and
// EasyPrivacy, cached under <AppDataLocation>/adblock/), the request
// interceptor installed on every profile, the per-site allow list and the
// blocked-request counters. Until the first download finishes, browsing works
// unfiltered.
class AdBlockManager : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    Q_PROPERTY(bool enabled READ enabled WRITE setEnabled NOTIFY enabledChanged)
    Q_PROPERTY(bool updating READ updating NOTIFY updatingChanged)
    Q_PROPERTY(QDateTime lastUpdate READ lastUpdate NOTIFY lastUpdateChanged)

public:
    static AdBlockManager *instance();
    static AdBlockManager *create(QQmlEngine *engine, QJSEngine *jsEngine);

    bool enabled() const;
    void setEnabled(bool enabled);
    bool updating() const { return m_pendingDownloads > 0; }
    QDateTime lastUpdate() const;

    // Installs the interceptor on a profile (normal and private ones).
    void install(QQuickWebEngineProfile *profile);
    // Loads the cached lists and refreshes them when older than four days.
    // Called once at startup, never from the constructor, so tests stay offline.
    void start();

    // Allow list changes from a private tab last for the session only.
    Q_INVOKABLE bool isAllowed(const QString &host) const;
    Q_INVOKABLE void setAllowed(const QString &host, bool allowed, bool persistent = true);
    Q_INVOKABLE int blockedCount(const QString &host) const;
    Q_INVOKABLE void updateLists();

    // Replaces the filter rules (also used by tests and the background loader).
    void setEngine(std::shared_ptr<const FilterEngine> engine);
    // Directory with the cached lists.
    static QString cacheDirectory();

signals:
    void enabledChanged();
    void updatingChanged();
    void lastUpdateChanged();
    void blockedCountChanged(const QString &host);
    // The allow list changed, persistently or for the session only.
    void allowListChanged();

private:
    explicit AdBlockManager(QObject *parent = nullptr);

    struct ListInfo {
        QString url;
        QString fileName;
    };
    static const QList<ListInfo> &lists();

    void syncAllowedHosts();
    void loadCachedLists();
    void download(const ListInfo &list);
    void downloadFinished();
    bool cacheIsStale() const;

    AdBlockInterceptor *m_interceptor;
    QNetworkAccessManager *m_network = nullptr;
    QHash<QString, int> m_counts;
    QSet<QString> m_sessionAllowed;
    QSet<QString> m_sessionBlocked;    // private-tab override of the persistent list
    int m_pendingDownloads = 0;
    bool m_downloadedAnything = false;
    bool m_reloadAfterLoad = false;
    QFutureWatcher<std::shared_ptr<const FilterEngine>> m_loader;
};
