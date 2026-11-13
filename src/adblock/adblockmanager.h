#pragma once

#include "adblock/adblockallowlist.h"
#include "adblock/filters/filterengine.h"

#include <QDateTime>
#include <QFutureWatcher>
#include <QHash>
#include <QObject>
#include <QString>
#include <QtQmlIntegration/qqmlintegration.h>

#include <memory>

class AdBlockInterceptor;
class FilterListDownloader;
class QQmlEngine;
class QJSEngine;
class QQuickWebEngineProfile;

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
    bool updating() const;
    QDateTime lastUpdate() const;

    void install(QQuickWebEngineProfile *profile);
    void start();

    Q_INVOKABLE bool isAllowed(const QString &host) const;
    Q_INVOKABLE void setAllowed(const QString &host, bool allowed, bool persistent = true);
    Q_INVOKABLE int blockedCount(const QString &host) const;
    Q_INVOKABLE void updateLists();

    void setEngine(std::shared_ptr<const FilterEngine> engine);
    static QString cacheDirectory();

signals:
    void enabledChanged();
    void updatingChanged();
    void lastUpdateChanged();
    void blockedCountChanged(const QString &host);
    void allowListChanged();

private:
    explicit AdBlockManager(QObject *parent = nullptr);

    void connectSettings();
    void connectInterceptor();
    void connectLoader();
    void connectDownloader();
    void syncAllowedHosts();
    void loadCachedLists();
    void countBlocked(const QString &host);
    void resetCount(const QString &host);
    void useLoadedEngine();
    void updateLastUpdateAndReload(bool isAnyListCurrent);

    AdBlockInterceptor *m_interceptor;
    FilterListDownloader *m_downloader;
    AdBlockAllowList m_allowList;
    QHash<QString, int> m_counts;
    bool m_reloadAfterLoad = false;
    QFutureWatcher<std::shared_ptr<const FilterEngine>> m_loader;
};
