#include "core/database/databasemigrations.h"

#include "core/database/defaultbookmarks.h"
#include "core/database/sql.h"

#include <QCoreApplication>
#include <QDateTime>
#include <QStringList>

namespace DatabaseMigrations {

namespace {

const QString kBookmarksTable = QStringLiteral(
    "CREATE TABLE IF NOT EXISTS bookmarks ("
    "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "  parent_id INTEGER REFERENCES bookmarks(id) ON DELETE CASCADE,"
    "  is_folder INTEGER NOT NULL DEFAULT 0,"
    "  title TEXT NOT NULL DEFAULT '',"
    "  url TEXT,"
    "  position INTEGER NOT NULL DEFAULT 0,"
    "  created_at INTEGER NOT NULL,"
    "  special TEXT)");

const QString kBookmarksIndex = QStringLiteral(
    "CREATE INDEX IF NOT EXISTS bookmarks_parent ON bookmarks(parent_id, position)");

bool runAll(const QStringList &statements)
{
    for (const QString &statement : statements) {
        if (!Sql::run(statement))
            return false;
    }
    return true;
}

bool insertRootFolder(const QString &title, const QString &special)
{
    return Sql::run(QStringLiteral(
        "INSERT INTO bookmarks (parent_id, is_folder, title, url, position,"
        " created_at, special) "
        "SELECT NULL, 1, ?, NULL, 0, ?, ? "
        "WHERE NOT EXISTS (SELECT 1 FROM bookmarks WHERE special = ?)"),
        {title, QDateTime::currentMSecsSinceEpoch(), special, special}).has_value();
}

bool hasUserBookmarks()
{
    auto query = Sql::run(QStringLiteral("SELECT 1 FROM bookmarks WHERE special IS NULL LIMIT 1"));
    return query && query->next();
}

QString displayTitle(const DefaultBookmark &row)
{
    if (row.isFolder())
        return QCoreApplication::translate("DefaultBookmarks", row.title);
    return QString::fromUtf8(row.title);
}

QVariant urlOf(const DefaultBookmark &row)
{
    return row.isFolder() ? QVariant() : QVariant(QString::fromUtf8(row.url));
}

std::optional<QVariant> insertDefaultBookmark(const DefaultBookmark &row, const QVariantList &place)
{
    auto insert = Sql::run(QStringLiteral(
        "INSERT INTO bookmarks (parent_id, is_folder, title, url, position,"
        " created_at, special) VALUES (?, ?, ?, ?, ?, ?, NULL)"),
        {place.at(0), row.isFolder() ? 1 : 0, displayTitle(row), urlOf(row), place.at(1),
         QDateTime::currentMSecsSinceEpoch()});
    if (!insert)
        return std::nullopt;
    return insert->lastInsertId();
}

bool insertDefaultRows(const QList<DefaultBookmark> &rows, const QVariant &parentId)
{
    for (int position = 0; position < rows.size(); ++position) {
        const DefaultBookmark &row = rows.at(position);
        const auto id = insertDefaultBookmark(row, {parentId, position});
        if (!id || !insertDefaultRows(row.children, *id))
            return false;
    }
    return true;
}

}

bool createHistoryTable()
{
    return runAll({
        QStringLiteral("CREATE TABLE IF NOT EXISTS history ("
                       "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
                       "  url TEXT NOT NULL,"
                       "  title TEXT NOT NULL DEFAULT '',"
                       "  visited_at INTEGER NOT NULL)"),
        QStringLiteral("CREATE INDEX IF NOT EXISTS history_visited_at ON history(visited_at DESC)"),
        QStringLiteral("CREATE INDEX IF NOT EXISTS history_url ON history(url)")});
}

bool createBookmarksTable()
{
    return runAll({kBookmarksTable, kBookmarksIndex});
}

bool createRootFolders()
{
    return insertRootFolder(QStringLiteral("Bookmarks Toolbar"), QStringLiteral("toolbar"))
        && insertRootFolder(QStringLiteral("Other Bookmarks"), QStringLiteral("other"));
}

bool createFaviconsTable()
{
    return Sql::run(QStringLiteral("CREATE TABLE IF NOT EXISTS favicons ("
                                   "  host TEXT PRIMARY KEY,"
                                   "  image BLOB NOT NULL,"
                                   "  updated_at INTEGER NOT NULL)")).has_value();
}

bool seedDefaultBookmarks()
{
    if (hasUserBookmarks())
        return true;
    const auto toolbar = Sql::ids(QStringLiteral("SELECT id FROM bookmarks WHERE special = 'toolbar' LIMIT 1"));
    return !toolbar.isEmpty() && insertDefaultRows(kDefaultBookmarks, toolbar.first());
}

bool createExtensionStorageTable()
{
    return Sql::run(QStringLiteral("CREATE TABLE IF NOT EXISTS extension_storage ("
                                   "  extension_id TEXT NOT NULL,"
                                   "  key TEXT NOT NULL,"
                                   "  value TEXT NOT NULL,"
                                   "  PRIMARY KEY (extension_id, key))")).has_value();
}

}
