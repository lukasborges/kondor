#include "adblockmanager.h"

#include "adblockinterceptor.h"
#include "settings.h"

#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QQuickWebEngineProfile>
#include <QSaveFile>
#include <QStandardPaths>
#include <QtConcurrent>

namespace {
constexpr int kMaxCacheAgeDays = 4;
}

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
{
    Settings *settings = Settings::instance();
    m_interceptor->setEnabled(settings->adBlockEnabled());
    syncAllowedHosts();

    connect(settings, &Settings::adBlockEnabledChanged, this, [this]() {
        m_interceptor->setEnabled(Settings::instance()->adBlockEnabled());
        emit enabledChanged();
    });
    connect(settings, &Settings::adBlockAllowListChanged, this, &AdBlockManager::syncAllowedHosts);
    connect(settings, &Settings::adBlockLastUpdateChanged, this, &AdBlockManager::lastUpdateChanged);

    connect(m_interceptor, &AdBlockInterceptor::blocked, this, [this](const QString &host) {
        ++m_counts[host];
        emit blockedCountChanged(host);
    });
    connect(m_interceptor, &AdBlockInterceptor::pageStarted, this, [this](const QString &host) {
        if (m_counts.value(host) == 0)
            return;
        m_counts[host] = 0;
        emit blockedCountChanged(host);
    });

    connect(&m_loader, &QFutureWatcher<std::shared_ptr<const FilterEngine>>::finished, this, [this]() {
        m_interceptor->setEngine(m_loader.result());
        if (m_reloadAfterLoad) {
            m_reloadAfterLoad = false;
            loadCachedLists();
        }
    });
}

const QList<AdBlockManager::ListInfo> &AdBlockManager::lists()
{
    static const QList<ListInfo> all = {
        {QStringLiteral("https://easylist.to/easylist/easylist.txt"), QStringLiteral("easylist.txt")},
        {QStringLiteral("https://easylist.to/easylist/easyprivacy.txt"),
         QStringLiteral("easyprivacy.txt")},
    };
    return all;
}

QString AdBlockManager::cacheDirectory()
{
    return QStandardPaths::writableLocation(QStandardPaths::AppDataLocation)
            + QStringLiteral("/adblock");
}

bool AdBlockManager::enabled() const
{
    return Settings::instance()->adBlockEnabled();
}

void AdBlockManager::setEnabled(bool enabled)
{
    Settings::instance()->setAdBlockEnabled(enabled);
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
    if (cacheIsStale())
        updateLists();
}

bool AdBlockManager::cacheIsStale() const
{
    const QDateTime last = lastUpdate();
    if (!last.isValid() || last.daysTo(QDateTime::currentDateTime()) >= kMaxCacheAgeDays)
        return true;
    for (const ListInfo &list : lists()) {
        if (!QFileInfo::exists(cacheDirectory() + QLatin1Char('/') + list.fileName))
            return true;
    }
    return false;
}

void AdBlockManager::setEngine(std::shared_ptr<const FilterEngine> engine)
{
    m_interceptor->setEngine(std::move(engine));
}

void AdBlockManager::loadCachedLists()
{
    if (m_loader.isRunning()) {
        m_reloadAfterLoad = true;
        return;
    }
    // Parsing 70k+ rules takes a moment: off the GUI thread, then swapped in.
    const QString directory = cacheDirectory();
    QStringList files;
    for (const ListInfo &list : lists())
        files.append(directory + QLatin1Char('/') + list.fileName);
    m_loader.setFuture(QtConcurrent::run([files]() {
        auto engine = std::make_shared<FilterEngine>();
        for (const QString &path : files) {
            QFile file(path);
            if (file.open(QIODevice::ReadOnly))
                engine->addList(file.readAll());
        }
        return std::shared_ptr<const FilterEngine>(std::move(engine));
    }));
}

void AdBlockManager::updateLists()
{
    if (m_pendingDownloads > 0)
        return;
    if (!m_network)
        m_network = new QNetworkAccessManager(this);
    QDir().mkpath(cacheDirectory());
    m_downloadedAnything = false;
    m_pendingDownloads = static_cast<int>(lists().size());
    emit updatingChanged();
    for (const ListInfo &list : lists())
        download(list);
}

void AdBlockManager::download(const ListInfo &list)
{
    const QString path = cacheDirectory() + QLatin1Char('/') + list.fileName;
    QNetworkRequest request{QUrl(list.url)};
    request.setAttribute(QNetworkRequest::RedirectPolicyAttribute,
                         QNetworkRequest::NoLessSafeRedirectPolicy);
    request.setTransferTimeout(60000);
    const QFileInfo info(path);
    if (info.exists()) {
        request.setHeader(QNetworkRequest::IfModifiedSinceHeader,
                          info.lastModified().toUTC());
    }
    QNetworkReply *reply = m_network->get(request);
    connect(reply, &QNetworkReply::finished, this, [this, reply, path]() {
        reply->deleteLater();
        const int status = reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt();
        if (reply->error() == QNetworkReply::NoError && status == 200) {
            const QByteArray body = reply->readAll();
            QSaveFile file(path);
            // A truncated or error page must not replace a good cached list.
            if (body.size() > 1024 && file.open(QIODevice::WriteOnly)) {
                file.write(body);
                if (file.commit())
                    m_downloadedAnything = true;
            }
        } else if (status == 304) {
            m_downloadedAnything = true;    // still current
        }
        downloadFinished();
    });
}

void AdBlockManager::downloadFinished()
{
    if (--m_pendingDownloads > 0)
        return;
    if (m_downloadedAnything) {
        Settings::instance()->setAdBlockLastUpdate(QDateTime::currentDateTime());
        loadCachedLists();
    }
    emit updatingChanged();
}

bool AdBlockManager::isAllowed(const QString &host) const
{
    const QString key = host.toLower();
    if (m_sessionBlocked.contains(key))
        return false;
    return Settings::instance()->adBlockAllowList().contains(key) || m_sessionAllowed.contains(key);
}

void AdBlockManager::setAllowed(const QString &host, bool allowed, bool persistent)
{
    const QString key = host.toLower();
    if (key.isEmpty())
        return;
    if (persistent) {
        QStringList list = Settings::instance()->adBlockAllowList();
        if (allowed && !list.contains(key))
            list.append(key);
        else if (!allowed)
            list.removeAll(key);
        // A persistent choice replaces any session-only one for the host.
        m_sessionAllowed.remove(key);
        m_sessionBlocked.remove(key);
        Settings::instance()->setAdBlockAllowList(list);
    } else if (allowed) {
        m_sessionAllowed.insert(key);
        m_sessionBlocked.remove(key);
    } else {
        // Session-only override that wins over the persistent list, which a
        // private tab never touches.
        m_sessionAllowed.remove(key);
        if (Settings::instance()->adBlockAllowList().contains(key))
            m_sessionBlocked.insert(key);
    }
    syncAllowedHosts();
    emit allowListChanged();
}

void AdBlockManager::syncAllowedHosts()
{
    QSet<QString> hosts = m_sessionAllowed;
    const QStringList persisted = Settings::instance()->adBlockAllowList();
    for (const QString &host : persisted)
        hosts.insert(host);
    for (const QString &host : std::as_const(m_sessionBlocked))
        hosts.remove(host);
    m_interceptor->setAllowedHosts(hosts);
}

int AdBlockManager::blockedCount(const QString &host) const
{
    return m_counts.value(host.toLower());
}
