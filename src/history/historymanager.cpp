#include "history/historymanager.h"

#include "browser/faviconstore.h"
#include "core/sql.h"
#include "history/historymodel.h"
#include "history/historysearch.h"
#include "history/topsitesranking.h"

#include <QDateTime>

namespace {
constexpr qint64 kRecentVisitWindowMs = 30000;
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
    const QString scheme = url.scheme();
    return !url.isEmpty()
        && (scheme == QLatin1String("http")
            || scheme == QLatin1String("https")
            || scheme == QLatin1String("file"));
}

std::optional<qint64> HistoryManager::recentVisitIdOf(const QString &url, qint64 now)
{
    auto last = Sql::run(QStringLiteral(
        "SELECT id, url, visited_at FROM history ORDER BY visited_at DESC, id DESC LIMIT 1"));
    if (!last || !last->next())
        return std::nullopt;
    const bool isSameUrl = last->value(1).toString() == url;
    const bool isRecent = now - last->value(2).toLongLong() < kRecentVisitWindowMs;
    if (!isSameUrl || !isRecent)
        return std::nullopt;
    return last->value(0).toLongLong();
}

void HistoryManager::updateTitleOf(qint64 id, const QString &title)
{
    Sql::run(QStringLiteral("UPDATE history SET title = ? WHERE id = ?"), {title, id});
}

bool HistoryManager::mergeIntoRecentVisit(const QString &url, const QString &title, qint64 now)
{
    const auto recentId = recentVisitIdOf(url, now);
    if (recentId)
        updateTitleOf(*recentId, title);
    return recentId.has_value();
}

bool HistoryManager::insertVisit(const QString &url, const QString &title, qint64 now)
{
    return Sql::run(QStringLiteral("INSERT INTO history (url, title, visited_at) VALUES (?, ?, ?)"),
                    {url, title, now}).has_value();
}

void HistoryManager::addVisit(const QUrl &url, const QString &title)
{
    if (!isTracked(url))
        return;
    const QString address = url.toString();
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    if (mergeIntoRecentVisit(address, title, now) || insertVisit(address, title, now))
        m_model->scheduleRefresh();
}

void HistoryManager::updateTitle(const QUrl &url, const QString &title)
{
    if (!isTracked(url))
        return;
    const QList<qint64> ids = Sql::ids(QStringLiteral(
        "SELECT id FROM history WHERE url = ? AND visited_at >= ?"
        " ORDER BY visited_at DESC, id DESC LIMIT 1"),
        {url.toString(), QDateTime::currentMSecsSinceEpoch() - kRecentVisitWindowMs});
    if (ids.isEmpty())
        return;
    updateTitleOf(ids.first(), title);
    m_model->scheduleRefresh();
}

void HistoryManager::removeEntry(qint64 id)
{
    if (Sql::run(QStringLiteral("DELETE FROM history WHERE id = ?"), {id}))
        m_model->refresh();
}

void HistoryManager::clearAll()
{
    if (!Sql::run(QStringLiteral("DELETE FROM history")))
        return;
    m_model->refresh();
    FaviconStore::instance()->clearAll();
}

void HistoryManager::clearSince(qint64 msecsSinceEpoch)
{
    if (!Sql::run(QStringLiteral("DELETE FROM history WHERE visited_at >= ?"), {msecsSinceEpoch}))
        return;
    m_model->refresh();
    FaviconStore::instance()->clearSince(msecsSinceEpoch);
}

QVariantList HistoryManager::topSites(int limit) const
{
    return TopSitesRanking::topSites(limit);
}

QVariantList HistoryManager::suggest(const QString &text, int limit) const
{
    return HistorySearch::suggest(text, limit);
}

QVariantList HistoryManager::recentToday(int limit) const
{
    return HistorySearch::recentToday(limit);
}

QString HistoryManager::hostCompletion(const QString &text) const
{
    return HistorySearch::hostCompletion(text);
}
