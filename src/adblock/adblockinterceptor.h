#pragma once

#include "adblock/filterengine.h"

#include <QReadWriteLock>
#include <QSet>
#include <QWebEngineUrlRequestInterceptor>

#include <atomic>
#include <memory>

class AdBlockInterceptor : public QWebEngineUrlRequestInterceptor
{
    Q_OBJECT

public:
    explicit AdBlockInterceptor(QObject *parent = nullptr);

    void interceptRequest(QWebEngineUrlRequestInfo &info) override;

    void setEngine(std::shared_ptr<const FilterEngine> engine);
    void setEnabled(bool enabled) { m_enabled = enabled; }
    void setAllowedHosts(const QSet<QString> &hosts);

signals:
    void blocked(const QString &firstPartyHost);
    void pageStarted(const QString &host);

private:
    void blockIfListed(QWebEngineUrlRequestInfo &info);
    bool isListed(const QWebEngineUrlRequestInfo &info, const QString &firstPartyHost) const;
    std::shared_ptr<const FilterEngine> engineUnlessAllowed(const QString &firstPartyHost) const;

    std::atomic<bool> m_enabled{true};
    mutable QReadWriteLock m_lock;
    std::shared_ptr<const FilterEngine> m_engine;
    QSet<QString> m_allowedHosts;
};
