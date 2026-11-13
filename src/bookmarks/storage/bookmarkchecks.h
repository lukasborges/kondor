#pragma once

#include <QVariantMap>

namespace BookmarkChecks {

bool isFolderId(qint64 id);
qint64 folderOrOtherBookmarks(qint64 folderId);
bool isSpecialRow(const QVariantMap &item);
bool canMove(const QVariantMap &item, qint64 newParentId);

}
