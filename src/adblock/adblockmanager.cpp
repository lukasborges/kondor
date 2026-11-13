#include "adblock/adblockmanager.h"

#include "adblock/adblockinterceptor.h"
#include "adblock/lists/filterlistdownloader.h"
#include "adblock/lists/filterlists.h"
#include "core/settings/settings.h"

#include <QQuickWebEngineProfile>
#include <QtConcurrent>

AdBlockManager *AdBlockManager::instance()
{
    static AdBlockManager *manager = new AdBlockManager;
    return manager;
}

AdBlockManager *AdBlockManager::create(QQmlEngine *engine, QJSEngine *jsEngine)
{
    Q_UNUSED(engine)
    Q_UNUSED(jsEngine)
    return instance();
}

AdBlockManager::AdBlockManager(QObject *parent)
    : QObject(parent)
    , m_interceptor(new AdBlockInterceptor(this))
    , m_downloader(new FilterListDownloader(this))
{
    m_interceptor->setEnabled(Settings::instance()->adBlockEnabled());
    syncAllowedHosts();
    connectSettings();
    connectInterceptor();
    connectLoader();
    connectDownloader();
}

void AdBlockManager::connectSettings()
{
    Settings *settings = Settings::instance();
    connect(settings, &Settings::adBlockEnabledChanged, this, [this]() {
        m_interceptor->setEnabled(Settings::instance()->adBlockEnabled());
        emit enabledChanged();
    });
    connect(settings, &Settings::adBlockAllowListChanged, this, &AdBlockManager::syncAllowedHosts);
    connect(settings, &Settings::adBlockLastUpdateChanged, this, &AdBlockManager::lastUpdateChanged);
}

void AdBlockManager::connectInterceptor()
{
    connect(m_interceptor, &AdBlockInterceptor::blocked, this, &AdBlockManager::countBlocked);
    connect(m_interceptor, &AdBlockInterceptor::pageStarted, this, &AdBlockManager::resetCount);
}

void AdBlockManager::connectLoader()
{
    connect(&m_loader, &QFutureWatcher<std::shared_ptr<const FilterEngine>>::finished, this,
            &AdBlockManager::useLoadedEngine);
}

void AdBlockManager::connectDownloader()
{
    connect(m_downloader, &FilterListDownloader::updatingChanged, this,
            &AdBlockManager::updatingChanged);
    connect(m_downloader, &FilterListDownloader::finished, this,
            [this](bool isAnyListCurrent) { updateLastUpdateAndReload(isAnyListCurrent); });
}

void AdBlockManager::countBlocked(const QString &host)
{
    ++m_counts[host];
    emit blockedCountChanged(host);
}

void AdBlockManager::resetCount(const QString &host)
{
    if (m_counts.value(host) == 0)
        return;
    m_counts[host] = 0;
    emit blockedCountChanged(host);
}

void AdBlockManager::useLoadedEngine()
{
    m_interceptor->setEngine(m_loader.result());
    if (!m_reloadAfterLoad)
        return;
    m_reloadAfterLoad = false;
    loadCachedLists();
}

void AdBlockManager::updateLastUpdateAndReload(bool isAnyListCurrent)
{
    if (!isAnyListCurrent)
        return;
    Settings::instance()->setAdBlockLastUpdate(QDateTime::currentDateTime());
    loadCachedLists();
}

QString AdBlockManager::cacheDirectory()
{
    return filterCacheDirectory();
}

bool AdBlockManager::enabled() const
{
    return Settings::instance()->adBlockEnabled();
}

void AdBlockManager::setEnabled(bool enabled)
{
    Settings::instance()->setAdBlockEnabled(enabled);
}

bool AdBlockManager::updating() const
{
    return m_downloader->isUpdating();
}

QDateTime AdBlockManager::lastUpdate() const
{
    return Settings::instance()->adBlockLastUpdate();
}

void AdBlockManager::install(QQuickWebEngineProfile *profile)
{
    profile->setUrlRequestInterceptor(m_interceptor);
}

void AdBlockManager::start()
{
    loadCachedLists();
    if (isCacheStale(lastUpdate()))
        updateLists();
}

void AdBlockManager::setEngine(std::shared_ptr<const FilterEngine> engine)
{
    m_interceptor->setEngine(std::move(engine));
}

void AdBlockManager::loadCachedLists()
{
    if (m_loader.isRunning())
        m_reloadAfterLoad = true;
    else
        m_loader.setFuture(QtConcurrent::run(parseFilterLists, cachedFilterListFiles()));
}

void AdBlockManager::updateLists()
{
    m_downloader->update();
}

bool AdBlockManager::isAllowed(const QString &host) const
{
    return m_allowList.isAllowed(host);
}

void AdBlockManager::setAllowed(const QString &host, bool allowed, bool persistent)
{
    if (host.isEmpty())
        return;
    if (persistent)
        m_allowList.setPersistent(host, allowed);
    else
        m_allowList.setForSession(host, allowed);
    syncAllowedHosts();
    emit allowListChanged();
}

void AdBlockManager::syncAllowedHosts()
{
    m_interceptor->setAllowedHosts(m_allowList.hosts());
}

int AdBlockManager::blockedCount(const QString &host) const
{
    return m_counts.value(host.toLower());
}
