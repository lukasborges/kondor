#pragma once

#include <QList>
#include <QString>
#include <QUrl>

struct ImportedBookmark {
    bool isFolder = false;
    QString title;
    QUrl url;
    QList<ImportedBookmark> children;
};

struct ParsedBookmarks {
    ImportedBookmark root;
    int bookmarkCount = 0;
};

namespace BookmarkHtmlParser {

ParsedBookmarks parse(const QString &html);

}
