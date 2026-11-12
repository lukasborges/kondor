#include "history/historymodel.h"

#include "core/database.h"

#include <QLocale>
#include <QSqlQuery>
#include <QVariant>

HistoryModel::HistoryModel(QObject *parent)
    : QAbstractListModel(parent)
{
    m_refreshTimer.setSingleShot(true);
    m_refreshTimer.setInterval(250);
    connect(&m_refreshTimer, &QTimer::timeout, this, &HistoryModel::refresh);
}

int HistoryModel::rowCount(const QModelIndex &parent) const
{
    return parent.isValid() ? 0 : int(m_entries.size());
}

QVariant HistoryModel::data(const QModelIndex &index, int role) const
{
    if (!index.isValid() || index.row() < 0 || index.row() >= m_entries.size())
        return {};

    const Entry &entry = m_entries.at(index.row());
    switch (role) {
    case IdRole:
        return entry.id;
    case UrlRole:
        return entry.url.toString();
    case TitleRole:
        return entry.title;
    case VisitedAtRole:
        return entry.visitedAt;
    case DayLabelRole:
        return entry.dayLabel;
    case TimeRole:
        return timeLabel(entry.visitedAt);
    default:
        return {};
    }
}

QHash<int, QByteArray> HistoryModel::roleNames() const
{
    return {
        {IdRole, "id"},
        {UrlRole, "url"},
        {TitleRole, "title"},
        {VisitedAtRole, "visitedAt"},
        {DayLabelRole, "dayLabel"},
        {TimeRole, "time"},
    };
}

void HistoryModel::setFilter(const QString &filter)
{
    if (m_filter == filter)
        return;
    m_filter = filter;
    emit filterChanged();
    refresh();
}

QString HistoryModel::urlAt(int index) const
{
    if (index < 0 || index >= m_entries.size())
        return {};
    return m_entries.at(index).url.toString();
}

void HistoryModel::setActive(bool active)
{
    if (m_active == active)
        return;
    m_active = active;
    emit activeChanged();
    if (m_active) {
        m_refreshTimer.stop();
        refresh();
    }
}

void HistoryModel::scheduleRefresh()
{
    // No view is showing the model: skip the query, it reloads on activation.
    if (!m_active)
        return;
    m_refreshTimer.start();
}

void HistoryModel::refresh()
{
    Database *db = Database::instance();
    QList<Entry> entries;

    if (db->isValid()) {
        const QString term = m_filter.trimmed();
        QString sql = QStringLiteral(
            "SELECT id, url, title, visited_at FROM history");
        if (!term.isEmpty())
            sql += QStringLiteral(" WHERE url LIKE ? ESCAPE '\\' OR title LIKE ? ESCAPE '\\'");
        sql += QStringLiteral(" ORDER BY visited_at DESC, id DESC LIMIT 500");

        QSqlQuery query(db->handle());
        query.prepare(sql);
        if (!term.isEmpty()) {
            const QString pattern = likePattern(term);
            query.addBindValue(pattern);
            query.addBindValue(pattern);
        }
        if (query.exec()) {
            while (query.next()) {
                Entry entry;
                entry.id = query.value(0).toLongLong();
                entry.url = QUrl(query.value(1).toString());
                entry.title = query.value(2).toString();
                entry.visitedAt = QDateTime::fromMSecsSinceEpoch(query.value(3).toLongLong());
                entry.dayLabel = dayLabel(entry.visitedAt);
                entries.append(entry);
            }
        }
    }

    beginResetModel();
    m_entries = entries;
    endResetModel();
    emit countChanged();
}

QString HistoryModel::likePattern(const QString &term)
{
    QString pattern;
    pattern.reserve(term.size() + 2);
    for (QChar c : term) {
        if (c == QLatin1Char('\\') || c == QLatin1Char('%') || c == QLatin1Char('_'))
            pattern.append(QLatin1Char('\\'));
        pattern.append(c);
    }
    pattern.prepend(QLatin1Char('%'));
    pattern.append(QLatin1Char('%'));
    return pattern;
}

QString HistoryModel::dayLabel(const QDateTime &time)
{
    const QDate date = time.date();
    const QDate today = QDate::currentDate();
    if (date == today)
        return tr("Today");
    if (date == today.addDays(-1))
        return tr("Yesterday");
    return QLocale().toString(date, QLocale::LongFormat);
}

QString HistoryModel::timeLabel(const QDateTime &time)
{
    return QLocale().toString(time.time(), QLocale::ShortFormat);
}
