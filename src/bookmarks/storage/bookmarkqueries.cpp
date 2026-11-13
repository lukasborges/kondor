#include "bookmarks/storage/bookmarkqueries.h"

#include "core/database/sql.h"

#include <QSqlQuery>

namespace BookmarkQueries {

namespace {

using RowReader = QVariantMap (*)(const QSqlQuery &);

QVariantList readRows(const QString &statement, const QVariantList &values, RowReader reader)
{
    QVariantList rows;
    auto query = Sql::run(statement, values);
    while (query && query->next())
        rows.append(reader(*query));
    return rows;
}

QVariantMap readFolderEntry(const QSqlQuery &query)
{
    return {{QStringLiteral("id"), query.value(0).toLongLong()},
            {QStringLiteral("title"), query.value(1).toString()},
            {QStringLiteral("url"), query.value(2).toString()},
            {QStringLiteral("isFolder"), query.value(3).toBool()}};
}

QVariantMap readBookmark(const QSqlQuery &query)
{
    return {{QStringLiteral("id"), query.value(0).toLongLong()},
            {QStringLiteral("parentId"), query.value(1).toLongLong()},
            {QStringLiteral("title"), query.value(2).toString()},
            {QStringLiteral("url"), query.value(3).toString()},
            {QStringLiteral("isFolder"), query.value(4).toBool()},
            {QStringLiteral("position"), query.value(5).toInt()},
            {QStringLiteral("special"), query.value(6).toString()}};
}

QVariantMap readSearchResult(const QSqlQuery &query)
{
    return {{QStringLiteral("type"), QStringLiteral("bookmark")},
            {QStringLiteral("url"), query.value(0).toString()},
            {QStringLiteral("title"), query.value(1).toString()}};
}

}

QVariantMap bookmark(qint64 id)
{
    if (id <= 0)
        return {};
    const QVariantList rows = readRows(
        QStringLiteral("SELECT id, parent_id, title, url, is_folder, position, special"
                       " FROM bookmarks WHERE id = ?"),
        {id}, readBookmark);
    return rows.isEmpty() ? QVariantMap() : rows.first().toMap();
}

QVariantList folderContents(qint64 folderId)
{
    if (folderId <= 0)
        return {};
    return readRows(QStringLiteral("SELECT id, title, url, is_folder FROM bookmarks"
                                   " WHERE parent_id = ? ORDER BY position, id"),
                    {folderId}, readFolderEntry);
}

int childCount(qint64 folderId)
{
    if (folderId <= 0)
        return 0;
    auto query = Sql::run(QStringLiteral("SELECT COUNT(*) FROM bookmarks WHERE parent_id = ?"),
                          {folderId});
    return query && query->next() ? query->value(0).toInt() : 0;
}

QString likePattern(const QString &term)
{
    QString escaped = term;
    escaped.replace(QLatin1String("\\"), QLatin1String("\\\\"));
    escaped.replace(QLatin1String("%"), QLatin1String("\\%"));
    escaped.replace(QLatin1String("_"), QLatin1String("\\_"));
    return QLatin1Char('%') + escaped + QLatin1Char('%');
}

QVariantList search(const QString &text, int limit)
{
    const QString needle = text.trimmed();
    if (needle.isEmpty() || limit <= 0)
        return {};
    const QString pattern = likePattern(needle);
    return readRows(
        QStringLiteral(
            "SELECT url, title FROM bookmarks"
            " WHERE is_folder = 0 AND (url LIKE ? ESCAPE '\\' OR title LIKE ? ESCAPE '\\')"
            " ORDER BY (title LIKE ? ESCAPE '\\') DESC, title COLLATE NOCASE, id LIMIT ?"),
        {pattern, pattern, pattern, limit}, readSearchResult);
}

qint64 bookmarkIdFor(const QUrl &url)
{
    if (url.isEmpty())
        return -1;
    return Sql::ids(QStringLiteral("SELECT id FROM bookmarks"
                                   " WHERE is_folder = 0 AND url = ? ORDER BY id LIMIT 1"),
                    {url.toString()})
        .value(0, -1);
}

bool isBookmarked(const QUrl &url)
{
    return bookmarkIdFor(url) > 0;
}

qint64 specialFolderId(const QString &special)
{
    return Sql::ids(QStringLiteral("SELECT id FROM bookmarks WHERE special = ? LIMIT 1"),
                    {special})
        .value(0, -1);
}

}
