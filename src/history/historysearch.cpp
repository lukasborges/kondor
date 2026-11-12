#include "history/historysearch.h"

#include "core/sql.h"

#include <QDate>
#include <QDateTime>
#include <QTime>
#include <QUrl>
#include <QVariantMap>

namespace HistorySearch {

namespace {

constexpr int kHostCompletionCandidates = 50;

QVariantMap suggestionOf(QSqlQuery &query)
{
    return {
        {QStringLiteral("type"), QStringLiteral("history")},
        {QStringLiteral("url"), query.value(0).toString()},
        {QStringLiteral("title"), query.value(1).toString()},
    };
}

QVariantMap recentEntryOf(QSqlQuery &query)
{
    return {
        {QStringLiteral("url"), query.value(0).toString()},
        {QStringLiteral("title"), query.value(1).toString()},
    };
}

QString hostWithoutWww(const QVariant &suggestion)
{
    QString host = QUrl(suggestion.toMap().value(QStringLiteral("url")).toString()).host();
    if (host.startsWith(QLatin1String("www.")))
        host.remove(0, 4);
    return host;
}

bool completesPrefix(const QString &host, const QString &prefix)
{
    return host.length() > prefix.length()
        && host.startsWith(prefix, Qt::CaseInsensitive);
}

std::optional<QSqlQuery> matchingVisits(const QString &needle, int limit)
{
    const QString pattern = HistorySearch::likePattern(needle);
    return Sql::run(QStringLiteral(
        "SELECT url, title, COUNT(*) AS visits, MAX(visited_at) AS last"
        " FROM history WHERE url LIKE ? ESCAPE '\\' OR title LIKE ? ESCAPE '\\'"
        " GROUP BY url ORDER BY visits DESC, last DESC LIMIT ?"),
        {pattern, pattern, limit});
}

qint64 localMidnight()
{
    return QDateTime(QDate::currentDate(), QTime(0, 0)).toMSecsSinceEpoch();
}

}

QString likePattern(const QString &term)
{
    QString escaped = term;
    escaped.replace(QLatin1String("\\"), QLatin1String("\\\\"));
    escaped.replace(QLatin1String("%"), QLatin1String("\\%"));
    escaped.replace(QLatin1String("_"), QLatin1String("\\_"));
    return QLatin1Char('%') + escaped + QLatin1Char('%');
}

QVariantList suggest(const QString &text, int limit)
{
    QVariantList suggestions;
    const QString needle = text.trimmed();
    if (needle.isEmpty() || limit <= 0)
        return suggestions;
    auto query = matchingVisits(needle, limit);
    while (query && query->next())
        suggestions.append(suggestionOf(*query));
    return suggestions;
}

QVariantList recentToday(int limit)
{
    QVariantList entries;
    if (limit <= 0)
        return entries;
    auto query = Sql::run(QStringLiteral(
        "SELECT url, title, MAX(visited_at) AS last FROM history WHERE visited_at >= ?"
        " GROUP BY url ORDER BY last DESC LIMIT ?"),
        {localMidnight(), limit});
    while (query && query->next())
        entries.append(recentEntryOf(*query));
    return entries;
}

QString hostCompletion(const QString &text)
{
    const QString prefix = text.trimmed();
    if (prefix.isEmpty() || prefix.contains(QLatin1Char(' ')))
        return QString();
    for (const QVariant &suggestion : suggest(prefix, kHostCompletionCandidates)) {
        const QString host = hostWithoutWww(suggestion);
        if (completesPrefix(host, prefix))
            return host;
    }
    return QString();
}

}
