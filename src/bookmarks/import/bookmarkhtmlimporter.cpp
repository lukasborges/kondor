#include "bookmarks/import/bookmarkhtmlimporter.h"

#include "bookmarks/storage/bookmarkfoldertree.h"
#include "bookmarks/storage/bookmarkqueries.h"
#include "core/database/sql.h"

#include <QHash>

namespace BookmarkHtmlImporter {

namespace {

constexpr auto kImportedFolderTitle = "Imported";

class TreeInserter {
public:
    void insertChildren(const ImportedBookmark &parent, qint64 parentId)
    {
        for (const ImportedBookmark &child : parent.children)
            insert(child, parentId);
    }

    int insertedBookmarks() const { return m_insertedBookmarks; }

private:
    void insert(const ImportedBookmark &node, qint64 parentId)
    {
        const BookmarkRow row{node.isFolder, node.title, node.url, parentId,
                              m_positions[parentId]++};
        const qint64 id = BookmarkFolderTree::insertRow(row);
        if (id <= 0)
            return;
        if (node.isFolder)
            insertChildren(node, id);
        else
            ++m_insertedBookmarks;
    }

    QHash<qint64, int> m_positions;
    int m_insertedBookmarks = 0;
};

qint64 insertImportedFolder()
{
    const qint64 otherId = BookmarkQueries::specialFolderId(QStringLiteral("other"));
    const BookmarkRow row{true, QString::fromLatin1(kImportedFolderTitle), QUrl(), otherId,
                          BookmarkFolderTree::firstFreePosition(otherId)};
    return BookmarkFolderTree::insertRow(row);
}

bool insertAll(const ParsedBookmarks &parsed, int &insertedBookmarks)
{
    const qint64 importedFolder = insertImportedFolder();
    if (importedFolder <= 0)
        return false;
    TreeInserter inserter;
    inserter.insertChildren(parsed.root, importedFolder);
    insertedBookmarks = inserter.insertedBookmarks();
    return insertedBookmarks == parsed.bookmarkCount;
}

}

int import(const ParsedBookmarks &parsed)
{
    if (parsed.bookmarkCount == 0)
        return 0;
    int insertedBookmarks = 0;
    const bool isCommitted =
        Sql::inTransaction([&] { return insertAll(parsed, insertedBookmarks); });
    return isCommitted ? insertedBookmarks : 0;
}

}
