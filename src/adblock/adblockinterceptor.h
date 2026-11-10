#pragma once

#include "filterengine.h"

#include <QReadWriteLock>
#include <QSet>
#include <QWebEngineUrlRequestInterceptor>

#include <atomic>
#include <memory>

// Blocks requests that match the filter lists. `interceptRequest` runs on the
// IO thread, so every shared member is guarded; the signals are queued to the
// GUI thread by Qt because the object lives there.
class AdBlockInterceptor : public QWebEngineUrlRequestInterceptor
{
    Q_OBJECT

public:
    explicit AdBlockInterceptor(QObject *parent = nullptr);

    void interceptRequest(QWebEngineUrlRequestInfo &info) override;

    void setEngine(std::shared_ptr<const FilterEngine> engine);
    void setEnabled(bool enabled) { m_enabled = enabled; }
    // Hosts where nothing is blocked.
    void setAllowedHosts(const QSet<QString> &hosts);

signals:
    // A request of this first-party host was blocked.
    void blocked(const QString &firstPartyHost);
    // A new page started loading for this host: its counter starts over.
    void pageStarted(const QString &host);

private:
    std::atomic<bool> m_enabled{true};
    mutable QReadWriteLock m_lock;
    std::shared_ptr<const FilterEngine> m_engine;
    QSet<QString> m_allowedHosts;
};
