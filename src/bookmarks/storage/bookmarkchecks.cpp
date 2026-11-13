#include "bookmarks/storage/bookmarkchecks.h"

#include "bookmarks/storage/bookmarkfoldertree.h"
#include "bookmarks/storage/bookmarkqueries.h"

namespace BookmarkChecks {

bool isFolderId(qint64 id)
{
    return BookmarkQueries::bookmark(id).value(QStringLiteral("isFolder")).toBool();
}

qint64 folderOrOtherBookmarks(qint64 folderId)
{
    if (folderId > 0 && isFolderId(folderId))
        return folderId;
    return BookmarkQueries::specialFolderId(QStringLiteral("other"));
}

bool isSpecialRow(const QVariantMap &item)
{
    return !item.value(QStringLiteral("special")).toString().isEmpty();
}

bool canMove(const QVariantMap &item, qint64 newParentId)
{
    if (item.isEmpty() || isSpecialRow(item))
        return false;
    if (newParentId > 0 && !isFolderId(newParentId))
        return false;
    const qint64 id = item.value(QStringLiteral("id")).toLongLong();
    const bool isFolder = item.value(QStringLiteral("isFolder")).toBool();
    return !(isFolder && BookmarkFolderTree::isInSubtree(newParentId, id));
}

}
