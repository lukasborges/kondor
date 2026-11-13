#pragma once

#include <QList>

struct DefaultBookmark {
    const char *title;
    const char *url;
    QList<DefaultBookmark> children;

    bool isFolder() const { return url == nullptr; }
};

extern const QList<DefaultBookmark> kDefaultBookmarks;
