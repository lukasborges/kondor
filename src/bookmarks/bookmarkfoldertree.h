#pragma once

#include "bookmarks/bookmarkrow.h"

#include <QVariantList>

namespace BookmarkFolderTree {

QVariantList folders();
bool isInSubtree(qint64 folderId, qint64 ancestorId);
void renumber(qint64 parentId, qint64 movedId, int movedPosition);
int firstFreePosition(qint64 parentId);
qint64 insertRow(const BookmarkRow &row);
bool reparent(qint64 id, qint64 parentId);
bool removeSubtree(qint64 id);

}
