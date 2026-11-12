#pragma once

#include <QFile>
#include <QVariantMap>

#include <functional>

#include "bookmarks/bookmarkmanager.h"

inline const char sampleBookmarksHtml[] = R"(<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3 ADD_DATE="1">Bookmarks Toolbar</H3>
    <DL><p>
        <DT><A HREF="https://kde.org/" ADD_DATE="1">KDE &amp; Qt</A>
        <DT><H3 ADD_DATE="1">Nested</H3>
        <DL><p>
            <DT><A HREF="https://planet.kde.org/">Planet KDE</A>
        </DL><p>
    </DL><p>
    <DT><A HREF="https://bookmarks.example/emoji">Emoji &#128512; &#x1F600;</A>
    <DT><A HREF="place:type=6">Unsupported</A>
</DL><p>
)";

inline bool writeSampleBookmarksHtml(const QString &path)
{
    QFile file(path);
    return file.open(QIODevice::WriteOnly) && file.write(sampleBookmarksHtml) > 0;
}

inline qint64 folderIdMatching(const std::function<bool(const QVariantMap &)> &matches)
{
    const QVariantList folders = BookmarkManager::instance()->folders();
    for (const QVariant &row : folders) {
        if (matches(row.toMap()))
            return row.toMap().value(QStringLiteral("id")).toLongLong();
    }
    return -1;
}

inline bool hasTitle(const QVariantMap &folder, const QString &title)
{
    return folder.value(QStringLiteral("title")).toString() == title;
}

inline qint64 importedFolderId()
{
    return folderIdMatching([](const QVariantMap &f) { return hasTitle(f, QStringLiteral("Imported")); });
}

inline qint64 importedToolbarId()
{
    const qint64 imported = importedFolderId();
    return folderIdMatching([imported](const QVariantMap &f) {
        return hasTitle(f, QStringLiteral("Bookmarks Toolbar"))
            && f.value(QStringLiteral("parentId")).toLongLong() == imported;
    });
}

inline qint64 nestedFolderId()
{
    return folderIdMatching([](const QVariantMap &f) { return hasTitle(f, QStringLiteral("Nested")); });
}
