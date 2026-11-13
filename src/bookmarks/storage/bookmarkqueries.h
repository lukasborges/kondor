#pragma once

#include <QString>
#include <QUrl>
#include <QVariantList>
#include <QVariantMap>

namespace BookmarkQueries {

QVariantMap bookmark(qint64 id);
QVariantList folderContents(qint64 folderId);
int childCount(qint64 folderId);
QVariantList search(const QString &text, int limit);
qint64 bookmarkIdFor(const QUrl &url);
bool isBookmarked(const QUrl &url);
qint64 specialFolderId(const QString &special);
QString likePattern(const QString &term);

}
