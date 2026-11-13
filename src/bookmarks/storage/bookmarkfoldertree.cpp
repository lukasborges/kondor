#include "bookmarks/storage/bookmarkfoldertree.h"

#include "bookmarks/storage/bookmarkqueries.h"
#include "core/database/sql.h"

#include <QDateTime>
#include <QSqlError>
#include <QSqlQuery>

namespace BookmarkFolderTree {

namespace {

QString siblingsCondition(qint64 parentId)
{
    return parentId > 0 ? QStringLiteral("parent_id = ?") : QStringLiteral("parent_id IS NULL");
}

QVariantList siblingsValues(qint64 parentId)
{
    return parentId > 0 ? QVariantList{parentId} : QVariantList{};
}

QList<qint64> siblingIds(qint64 parentId)
{
    return Sql::ids(QStringLiteral("SELECT id FROM bookmarks WHERE ")
                        + siblingsCondition(parentId) + QStringLiteral(" ORDER BY position, id"),
                    siblingsValues(parentId));
}

void placeAt(QList<qint64> &order, qint64 movedId, int movedPosition)
{
    order.removeAll(movedId);
    const int size = int(order.size());
    order.insert(movedPosition < 0 ? size : qBound(0, movedPosition, size), movedId);
}

QList<qint64> specialRootIds()
{
    QList<qint64> roots;
    for (const char *special : {"toolbar", "other"}) {
        const qint64 id = BookmarkQueries::specialFolderId(QLatin1String(special));
        if (id > 0)
            roots.append(id);
    }
    return roots;
}

QList<qint64> rootFolderIds()
{
    QList<qint64> roots = specialRootIds();
    const QList<qint64> others = Sql::ids(QStringLiteral(
        "SELECT id FROM bookmarks WHERE parent_id IS NULL AND special IS NULL"
        " ORDER BY position, id"));
    for (qint64 id : others) {
        if (!roots.contains(id))
            roots.append(id);
    }
    return roots;
}

QVariantMap folderRow(const QSqlQuery &folder, int depth)
{
    return {{QStringLiteral("id"), folder.value(0).toLongLong()},
            {QStringLiteral("title"), folder.value(1).toString()},
            {QStringLiteral("parentId"), folder.value(2).toLongLong()},
            {QStringLiteral("depth"), depth}};
}

QList<qint64> childFolderIds(qint64 folderId)
{
    return Sql::ids(QStringLiteral("SELECT id FROM bookmarks WHERE parent_id = ? AND is_folder = 1"
                                   " ORDER BY position, id"),
                    {folderId});
}

void appendSubtree(qint64 folderId, int depth, QVariantList &rows)
{
    auto folder = Sql::run(QStringLiteral("SELECT id, title, COALESCE(parent_id, 0)"
                                          " FROM bookmarks WHERE id = ? AND is_folder = 1"),
                           {folderId});
    if (!folder || !folder->next())
        return;
    rows.append(folderRow(*folder, depth));
    for (qint64 childId : childFolderIds(folderId))
        appendSubtree(childId, depth + 1, rows);
}

QVariantList insertValues(const BookmarkRow &row)
{
    const QVariant url = row.isFolder || !row.url.isValid() ? QVariant() : row.url.toString();
    return {Sql::idOrNull(row.parentId), row.isFolder ? 1 : 0, row.title, url, row.position,
            QDateTime::currentMSecsSinceEpoch()};
}

}

QVariantList folders()
{
    QVariantList rows;
    for (qint64 root : rootFolderIds())
        appendSubtree(root, 0, rows);
    return rows;
}

bool isInSubtree(qint64 folderId, qint64 ancestorId)
{
    return !Sql::ids(QStringLiteral("WITH RECURSIVE subtree(id) AS ("
                                    "  SELECT id FROM bookmarks WHERE id = ?"
                                    "  UNION ALL"
                                    "  SELECT b.id FROM bookmarks b JOIN subtree s ON b.parent_id = s.id"
                                    ") SELECT 1 FROM subtree WHERE id = ? LIMIT 1"),
                     {ancestorId, folderId})
                .isEmpty();
}

void renumber(qint64 parentId, qint64 movedId, int movedPosition)
{
    QList<qint64> order = siblingIds(parentId);
    if (movedId > 0)
        placeAt(order, movedId, movedPosition);
    for (int position = 0; position < order.size(); ++position)
        Sql::run(QStringLiteral("UPDATE bookmarks SET position = ? WHERE id = ?"),
                 {position, order.at(position)});
}

int firstFreePosition(qint64 parentId)
{
    auto query = Sql::run(QStringLiteral("SELECT COALESCE(MAX(position), -1) + 1 FROM bookmarks"
                                         " WHERE ")
                              + siblingsCondition(parentId),
                          siblingsValues(parentId));
    return query && query->next() ? query->value(0).toInt() : 0;
}

qint64 insertRow(const BookmarkRow &row)
{
    auto query = Sql::run(
        QStringLiteral("INSERT INTO bookmarks (parent_id, is_folder, title, url, position,"
                       " created_at) VALUES (?, ?, ?, ?, ?, ?)"),
        insertValues(row));
    if (!query) {
        qWarning("Bookmarks: failed to insert %s", qPrintable(row.title));
        return -1;
    }
    return query->lastInsertId().toLongLong();
}

bool reparent(qint64 id, qint64 parentId)
{
    return Sql::run(QStringLiteral("UPDATE bookmarks SET parent_id = ? WHERE id = ?"),
                    {Sql::idOrNull(parentId), id})
        .has_value();
}

bool removeSubtree(qint64 id)
{
    return Sql::run(QStringLiteral("WITH RECURSIVE doomed(id) AS ("
                                   "  SELECT id FROM bookmarks WHERE id = ?"
                                   "  UNION ALL"
                                   "  SELECT b.id FROM bookmarks b JOIN doomed d ON b.parent_id = d.id"
                                   ") DELETE FROM bookmarks WHERE id IN (SELECT id FROM doomed)"),
                    {id})
        .has_value();
}

}
