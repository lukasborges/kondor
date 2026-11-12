#pragma once

#include <QTest>
#include <QUrl>

#include "bookmarks/bookmarkmanager.h"
#include "bookmarks/bookmarkmodel.h"

inline qint64 addPage(qint64 folderId, const QString &title, const QString &path)
{
    const QUrl url(QStringLiteral("https://bookmarks.example/") + path);
    return BookmarkManager::instance()->addBookmark(url, title, folderId);
}

inline qint64 addFolderInOther(const QString &title)
{
    BookmarkManager *manager = BookmarkManager::instance();
    return manager->addFolder(title, manager->otherFolderId());
}

inline qint64 parentOf(qint64 id)
{
    return BookmarkManager::instance()->bookmark(id).value(QStringLiteral("parentId")).toLongLong();
}

struct FolderWithPage
{
    qint64 folder;
    qint64 page;
};

inline FolderWithPage addFolderWithPage(const QString &folderTitle, const QString &pageTitle,
                                        const QString &path)
{
    const qint64 folder = addFolderInOther(folderTitle);
    return {folder, addPage(folder, pageTitle, path)};
}

struct ReorderedFolder
{
    qint64 folder;
    qint64 movedToTop;
    qint64 pushedDown;
};

inline ReorderedFolder reorderedFolder()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 folder = addFolderInOther(QStringLiteral("Moved"));
    const qint64 pushedDown = addPage(folder, QStringLiteral("Move me"), QStringLiteral("move"));
    const qint64 second = addPage(folder, QStringLiteral("Second"), QStringLiteral("second"));
    manager->move(second, folder, 0);
    return {folder, second, pushedDown};
}

inline void addSearchFixture()
{
    const qint64 folder = addFolderInOther(QStringLiteral("Search folder"));
    BookmarkManager *manager = BookmarkManager::instance();
    QVERIFY(manager->addBookmark(QUrl(QStringLiteral("https://searchable.example/")),
                                 QStringLiteral("Searchable Site"), folder) > 0);
    QVERIFY(manager->addBookmark(QUrl(QStringLiteral("https://other.example/unique-url")),
                                 QStringLiteral("Other"), folder) > 0);
}

inline void verifySearchByTitle()
{
    const QVariantList byTitle = BookmarkManager::instance()->search(QStringLiteral("searchable"));
    QCOMPARE(byTitle.size(), 1);
    const QVariantMap entry = byTitle.at(0).toMap();
    QCOMPARE(entry.value(QStringLiteral("type")).toString(), QStringLiteral("bookmark"));
    QCOMPARE(entry.value(QStringLiteral("title")).toString(), QStringLiteral("Searchable Site"));
    QCOMPARE(entry.value(QStringLiteral("url")).toString(), QStringLiteral("https://searchable.example/"));
}

inline void verifySearchByUrl()
{
    const QVariantList byUrl = BookmarkManager::instance()->search(QStringLiteral("unique-url"));
    QCOMPARE(byUrl.size(), 1);
    QCOMPARE(byUrl.at(0).toMap().value(QStringLiteral("title")).toString(), QStringLiteral("Other"));
}

inline void verifySearchSkipsFoldersAndHonoursLimit()
{
    BookmarkManager *manager = BookmarkManager::instance();
    QVERIFY(manager->search(QStringLiteral("Search folder")).isEmpty());
    QCOMPARE(manager->search(QStringLiteral("e"), 1).size(), 1);
    QVERIFY(manager->search(QStringLiteral("   ")).isEmpty());
}

inline void verifySameUrlInToolbarGetsItsOwnId(const QUrl &url, qint64 first)
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 toolbar = manager->toolbarFolderId();
    const int toolbarChildren = manager->childCount(toolbar);
    const qint64 second = manager->addBookmark(url, QStringLiteral("Page again"), toolbar);
    QVERIFY(second > 0);
    QVERIFY(second != first);
    QCOMPARE(manager->childCount(toolbar), toolbarChildren + 1);
}
