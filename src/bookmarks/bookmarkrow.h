#pragma once

#include <QString>
#include <QUrl>

struct BookmarkRow {
    bool isFolder = false;
    QString title;
    QUrl url;
    qint64 parentId = 0;
    int position = 0;
};

inline bool isSupportedBookmarkUrl(const QUrl &url)
{
    const QString scheme = url.scheme();
    return !url.isEmpty()
        && (scheme == QLatin1String("http") || scheme == QLatin1String("https")
            || scheme == QLatin1String("file"));
}
