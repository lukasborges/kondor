#include "historymanager.h"

#include "database.h"
#include "historymodel.h"
#include "settings.h"

#include <QDateTime>
#include <QHash>
#include <QList>
#include <QSqlQuery>
#include <QVariant>
#include <QVariantMap>

#include <algorithm>

namespace {
// A visit is "recent" within this window: consecutive visits to the same URL
// dedupe into one row, and updateTitle only touches visits this recent.
constexpr qint64 kRecentVisitWindowMs = 30000;
// The New Tab page only considers recent browsing.
constexpr qint64 kTopSitesWindowMs = 90LL * 24 * 60 * 60 * 1000;
}

HistoryManager *HistoryManager::instance()
{
    static HistoryManager *manager = new HistoryManager;
    return manager;
}

HistoryManager *HistoryManager::create(QQmlEngine *engine, QJSEngine *jsEngine)
{
    Q_UNUSED(engine)
    Q_UNUSED(jsEngine)
    return instance();
}

HistoryManager::HistoryManager(QObject *parent)
    : QObject(parent)
    , m_model(new HistoryModel(this))
{
}

HistoryModel *HistoryManager::model() const
{
    return m_model;
}

bool HistoryManager::isTracked(const QUrl &url)
{
    if (url.isEmpty())
        return false;
    const QString scheme = url.scheme();
    return scheme == QLatin1String("http")
        || scheme == QLatin1String("https")
        || scheme == QLatin1String("file");
}

void HistoryManager::addVisit(const QUrl &url, const QString &title)
{
    Database *db = Database::instance();
    if (!db->isValid() || !isTracked(url))
        return;

    const QString urlStr = url.toString();
    const qint64 now = QDateTime::currentMSecsSinceEpoch();

    QSqlQuery last(db->handle());
    last.prepare(QStringLiteral(
        "SELECT id, url, visited_at FROM history ORDER BY visited_at DESC, id DESC LIMIT 1"));
    if (last.exec() && last.next()) {
        const qint64 lastTime = last.value(2).toLongLong();
        if (last.value(1).toString() == urlStr && (now - lastTime) < kRecentVisitWindowMs) {
            QSqlQuery update(db->handle());
            update.prepare(QStringLiteral("UPDATE history SET title = ? WHERE id = ?"));
            update.addBindValue(title);
            update.addBindValue(last.value(0));
            update.exec();
            m_model->scheduleRefresh();
            return;
        }
    }

    QSqlQuery insert(db->handle());
    insert.prepare(QStringLiteral(
        "INSERT INTO history (url, title, visited_at) VALUES (?, ?, ?)"));
    insert.addBindValue(urlStr);
    insert.addBindValue(title);
    insert.addBindValue(now);
    if (insert.exec())
        m_model->scheduleRefresh();
}

void HistoryManager::updateTitle(const QUrl &url, const QString &title)
{
    Database *db = Database::instance();
    if (!db->isValid() || !isTracked(url))
        return;

    // Only update the current navigation's visit. `titleChanged` can fire before
    // `loadFinished`, so restricting to recent visits keeps an older row for the
    // same URL (e.g. yesterday's) untouched.
    QSqlQuery find(db->handle());
    find.prepare(QStringLiteral(
        "SELECT id FROM history WHERE url = ? AND visited_at >= ?"
        " ORDER BY visited_at DESC, id DESC LIMIT 1"));
    find.addBindValue(url.toString());
    find.addBindValue(QDateTime::currentMSecsSinceEpoch() - kRecentVisitWindowMs);
    if (find.exec() && find.next()) {
        QSqlQuery update(db->handle());
        update.prepare(QStringLiteral("UPDATE history SET title = ? WHERE id = ?"));
        update.addBindValue(title);
        update.addBindValue(find.value(0));
        if (update.exec())
            m_model->scheduleRefresh();
    }
}

void HistoryManager::removeEntry(qint64 id)
{
    Database *db = Database::instance();
    if (!db->isValid())
        return;
    QSqlQuery query(db->handle());
    query.prepare(QStringLiteral("DELETE FROM history WHERE id = ?"));
    query.addBindValue(id);
    if (query.exec())
        m_model->refresh();
}

void HistoryManager::clearAll()
{
    Database *db = Database::instance();
    if (!db->isValid())
        return;
    QSqlQuery query(db->handle());
    if (query.exec(QStringLiteral("DELETE FROM history")))
        m_model->refresh();
}

void HistoryManager::clearSince(qint64 msecsSinceEpoch)
{
    Database *db = Database::instance();
    if (!db->isValid())
        return;
    QSqlQuery query(db->handle());
    query.prepare(QStringLiteral("DELETE FROM history WHERE visited_at >= ?"));
    query.addBindValue(msecsSinceEpoch);
    if (query.exec())
        m_model->refresh();
}

QVariantList HistoryManager::topSites(int limit) const
{
    QVariantList sites;
    Database *db = Database::instance();
    if (!db->isValid() || limit <= 0)
        return sites;

    struct UrlStats {
        int visits = 0;
        qint64 lastVisit = 0;
        QString title;
    };
    struct HostStats {
        int score = 0;
        qint64 lastVisit = 0;
        QHash<QString, UrlStats> urls;
    };

    QSqlQuery query(db->handle());
    query.prepare(QStringLiteral(
        "SELECT url, title, visited_at FROM history WHERE visited_at >= ?"
        " ORDER BY visited_at DESC, id DESC"));
    query.addBindValue(QDateTime::currentMSecsSinceEpoch() - kTopSitesWindowMs);
    if (!query.exec())
        return sites;

    // Rows come newest first, so the first non-empty title seen for a URL is
    // its latest one.
    QHash<QString, HostStats> hosts;
    while (query.next()) {
        const QUrl url(query.value(0).toString());
        const QString scheme = url.scheme();
        if (scheme != QLatin1String("http") && scheme != QLatin1String("https"))
            continue;
        QString host = url.host();
        if (host.startsWith(QLatin1String("www.")))
            host.remove(0, 4);
        if (host.isEmpty())
            continue;

        const qint64 visitedAt = query.value(2).toLongLong();
        const QString urlString = url.toString();
        const QString title = query.value(1).toString();

        HostStats &hostStats = hosts[host];
        ++hostStats.score;
        hostStats.lastVisit = qMax(hostStats.lastVisit, visitedAt);

        UrlStats &urlStats = hostStats.urls[urlString];
        ++urlStats.visits;
        urlStats.lastVisit = qMax(urlStats.lastVisit, visitedAt);
        if (urlStats.title.isEmpty() && !title.isEmpty())
            urlStats.title = title;
    }

    struct Entry {
        QString host;
        QString url;
        QString title;
        int score = 0;
        qint64 lastVisit = 0;
    };

    const QStringList hidden = Settings::instance()->hiddenTopSites();
    QList<Entry> entries;
    entries.reserve(hosts.size());
    for (auto hostIt = hosts.constBegin(); hostIt != hosts.constEnd(); ++hostIt) {
        if (hidden.contains(hostIt.key()))
            continue;

        // The tile points at the host's most visited URL; on a tie, the most
        // recently visited one.
        const UrlStats *best = nullptr;
        QString bestUrl;
        for (auto urlIt = hostIt.value().urls.constBegin();
             urlIt != hostIt.value().urls.constEnd(); ++urlIt) {
            const UrlStats &candidate = urlIt.value();
            if (!best || candidate.visits > best->visits
                    || (candidate.visits == best->visits && candidate.lastVisit > best->lastVisit)) {
                best = &candidate;
                bestUrl = urlIt.key();
            }
        }
        if (!best)
            continue;

        Entry entry;
        entry.host = hostIt.key();
        entry.url = bestUrl;
        entry.title = best->title;
        entry.score = hostIt.value().score;
        entry.lastVisit = hostIt.value().lastVisit;
        entries.append(entry);
    }

    std::sort(entries.begin(), entries.end(), [](const Entry &a, const Entry &b) {
        if (a.score != b.score)
            return a.score > b.score;
        return a.lastVisit > b.lastVisit;
    });

    const int count = qMin(limit, int(entries.size()));
    sites.reserve(count);
    for (int i = 0; i < count; ++i) {
        const Entry &entry = entries.at(i);
        QVariantMap site;
        site.insert(QStringLiteral("url"), entry.url);
        site.insert(QStringLiteral("title"), entry.title);
        site.insert(QStringLiteral("host"), entry.host);
        sites.append(site);
    }
    return sites;
}
