#include "history/historymodel.h"

#include "core/sql.h"
#include "history/historysearch.h"

#include <QLocale>
#include <QVariant>

namespace {

constexpr int kRefreshDebounceMs = 250;
constexpr int kMaxEntries = 500;

QString selectEntriesStatement(bool isFiltered)
{
    QString statement = QStringLiteral("SELECT id, url, title, visited_at FROM history");
    if (isFiltered)
        statement += QStringLiteral(" WHERE url LIKE ? ESCAPE '\\' OR title LIKE ? ESCAPE '\\'");
    return statement + QStringLiteral(" ORDER BY visited_at DESC, id DESC LIMIT %1").arg(kMaxEntries);
}

QString dayLabelOf(const QDateTime &time)
{
    const QDate date = time.date();
    const QDate today = QDate::currentDate();
    if (date == today)
        return HistoryModel::tr("Today");
    if (date == today.addDays(-1))
        return HistoryModel::tr("Yesterday");
    return QLocale().toString(date, QLocale::LongFormat);
}

QString timeLabelOf(const QDateTime &time)
{
    return QLocale().toString(time.time(), QLocale::ShortFormat);
}

}

HistoryModel::HistoryModel(QObject *parent)
    : QAbstractListModel(parent)
{
    m_refreshTimer.setSingleShot(true);
    m_refreshTimer.setInterval(kRefreshDebounceMs);
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
    return roleValue(m_entries.at(index.row()), role);
}

QVariant HistoryModel::roleValue(const Entry &entry, int role)
{
    switch (role) {
    case IdRole: return entry.id;
    case UrlRole: return entry.url.toString();
    case TitleRole: return entry.title;
    case VisitedAtRole: return entry.visitedAt;
    case DayLabelRole: return entry.dayLabel;
    case TimeRole: return timeLabelOf(entry.visitedAt);
    default: return {};
    }
}

QHash<int, QByteArray> HistoryModel::roleNames() const
{
    static const QHash<int, QByteArray> names = {
        {IdRole, "id"},
        {UrlRole, "url"},
        {TitleRole, "title"},
        {VisitedAtRole, "visitedAt"},
        {DayLabelRole, "dayLabel"},
        {TimeRole, "time"},
    };
    return names;
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
    if (!m_active)
        return;
    m_refreshTimer.stop();
    refresh();
}

void HistoryModel::scheduleRefresh()
{
    if (m_active)
        m_refreshTimer.start();
}

void HistoryModel::refresh()
{
    const QList<Entry> entries = loadEntries();
    beginResetModel();
    m_entries = entries;
    endResetModel();
    emit countChanged();
}

std::optional<QSqlQuery> HistoryModel::queryEntries() const
{
    const QString term = m_filter.trimmed();
    if (term.isEmpty())
        return Sql::run(selectEntriesStatement(false));
    const QString pattern = HistorySearch::likePattern(term);
    return Sql::run(selectEntriesStatement(true), {pattern, pattern});
}

QList<HistoryModel::Entry> HistoryModel::loadEntries() const
{
    QList<Entry> entries;
    auto rows = queryEntries();
    while (rows && rows->next())
        entries.append(entryOf(*rows));
    return entries;
}

HistoryModel::Entry HistoryModel::entryOf(QSqlQuery &row)
{
    const QDateTime visitedAt = QDateTime::fromMSecsSinceEpoch(row.value(3).toLongLong());
    return {row.value(0).toLongLong(), QUrl(row.value(1).toString()),
            row.value(2).toString(), visitedAt, dayLabelOf(visitedAt)};
}
