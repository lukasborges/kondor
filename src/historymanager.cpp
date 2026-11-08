#include "historymanager.h"

#include "database.h"
#include "historymodel.h"

#include <QDateTime>
#include <QSqlQuery>
#include <QVariant>

namespace {
// A visit is "recent" within this window: consecutive visits to the same URL
// dedupe into one row, and updateTitle only touches visits this recent.
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
