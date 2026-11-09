#include <QDir>
#include <QFile>
#include <QSqlQuery>
#include <QStandardPaths>
#include <QTemporaryDir>
#include <QTest>
#include <QVariantMap>

#include "bookmarkmanager.h"
#include "bookmarkmodel.h"
#include "database.h"

class TestBookmarks : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void rootFolders();
    void addAndFindBookmarks();
    void moveBetweenFolders();
    void moveIntoAnotherFolderAtEnd();
    void refuseMovingFolderIntoChild();
    void modelFollowsSelectedFolder();
    void removeFolderCascades();
    void importNetscapeHtml();
};

void TestBookmarks::initTestCase()
{
    QVERIFY2(Database::instance()->isValid(), "the test database must open");
}

void TestBookmarks::rootFolders()
{
    BookmarkManager *manager = BookmarkManager::instance();
    QVERIFY(manager->toolbarFolderId() > 0);
    QVERIFY(manager->otherFolderId() > 0);
    QVERIFY(manager->toolbarFolderId() != manager->otherFolderId());
    // The bar lists the "Bookmarks Toolbar" folder.
    QCOMPARE(manager->toolbarModel()->folderId(), manager->toolbarFolderId());
}

void TestBookmarks::addAndFindBookmarks()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const QUrl url(QStringLiteral("https://bookmarks.example/page"));
    QVERIFY(!manager->isBookmarked(url));

    const qint64 other = manager->otherFolderId();
    const qint64 first = manager->addBookmark(url, QStringLiteral("Page"), other);
    QVERIFY(first > 0);
    QVERIFY(manager->isBookmarked(url));
    QCOMPARE(manager->bookmarkIdFor(url), first);

    // The same URL is allowed in another folder; the star still finds one id.
    const qint64 toolbar = manager->toolbarFolderId();
    const qint64 second = manager->addBookmark(url, QStringLiteral("Page again"), toolbar);
    QVERIFY(second > 0);
    QVERIFY(second != first);
    QCOMPARE(manager->childCount(toolbar), 1);

    const QVariantMap info = manager->bookmark(first);
    QCOMPARE(info.value(QStringLiteral("parentId")).toLongLong(), other);
    QCOMPARE(info.value(QStringLiteral("title")).toString(), QStringLiteral("Page"));
}

void TestBookmarks::moveBetweenFolders()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 folder = manager->addFolder(QStringLiteral("Moved"), manager->otherFolderId());
    QVERIFY(folder > 0);

    const QUrl url(QStringLiteral("https://bookmarks.example/move"));
    const qint64 id = manager->addBookmark(url, QStringLiteral("Move me"),
                                           manager->otherFolderId());
    QVERIFY(id > 0);

    manager->move(id, folder, -1);
    QCOMPARE(manager->bookmark(id).value(QStringLiteral("parentId")).toLongLong(), folder);
    QCOMPARE(manager->childCount(folder), 1);

    // Sorting inside the folder: the second item moves above the first.
    const qint64 second = manager->addBookmark(QUrl(QStringLiteral("https://bookmarks.example/second")),
                                               QStringLiteral("Second"), folder);
    QVERIFY(second > 0);
    manager->move(second, folder, 0);
    const QVariantList contents = manager->folderContents(folder);
    QCOMPARE(contents.size(), 2);
    QCOMPARE(contents.first().toMap().value(QStringLiteral("id")).toLongLong(), second);

    // The model reports the moved bookmark's row, which the manager window
    // uses to keep the selection on it.
    BookmarkModel *model = manager->modelForFolder(folder);
    QCOMPARE(model->rowOf(second), 0);
    QCOMPARE(model->idAt(0), second);
    QCOMPARE(model->rowOf(id), 1);
    QCOMPARE(model->rowOf(999999), -1);

    // A folder cannot be moved into itself.
    manager->move(folder, folder, 0);
    QCOMPARE(manager->bookmark(folder).value(QStringLiteral("parentId")).toLongLong(),
             manager->otherFolderId());
}

void TestBookmarks::moveIntoAnotherFolderAtEnd()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 target = manager->addFolder(QStringLiteral("Move target"),
                                             manager->otherFolderId());
    QVERIFY(target > 0);
    const qint64 first = manager->addBookmark(QUrl(QStringLiteral("https://bookmarks.example/end-a")),
                                              QStringLiteral("End A"), target);
    QVERIFY(first > 0);

    const qint64 source = manager->addFolder(QStringLiteral("Move source"),
                                             manager->otherFolderId());
    QVERIFY(source > 0);
    const qint64 moved = manager->addBookmark(QUrl(QStringLiteral("https://bookmarks.example/end-b")),
                                              QStringLiteral("End B"), source);
    QVERIFY(moved > 0);

    // The drag and drop and "Move To" code appends at the current child count.
    manager->move(moved, target, manager->childCount(target));
    QCOMPARE(manager->bookmark(moved).value(QStringLiteral("parentId")).toLongLong(), target);
    QCOMPARE(manager->bookmark(moved).value(QStringLiteral("position")).toInt(), 1);
    QCOMPARE(manager->childCount(source), 0);

    // The target folder's model shows the new order.
    BookmarkModel *model = manager->modelForFolder(target);
    QCOMPARE(model->rowOf(first), 0);
    QCOMPARE(model->rowOf(moved), 1);
}

void TestBookmarks::refuseMovingFolderIntoChild()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 parent = manager->addFolder(QStringLiteral("Cycle parent"),
                                             manager->otherFolderId());
    QVERIFY(parent > 0);
    const qint64 child = manager->addFolder(QStringLiteral("Cycle child"), parent);
    QVERIFY(child > 0);
    const qint64 grandchild = manager->addFolder(QStringLiteral("Cycle grandchild"), child);
    QVERIFY(grandchild > 0);

    // Moving a folder into its own subtree would detach it: refused.
    manager->move(parent, grandchild, 0);
    QCOMPARE(manager->bookmark(parent).value(QStringLiteral("parentId")).toLongLong(),
             manager->otherFolderId());
    QCOMPARE(manager->bookmark(child).value(QStringLiteral("parentId")).toLongLong(), parent);
    QCOMPARE(manager->bookmark(grandchild).value(QStringLiteral("parentId")).toLongLong(), child);
}

void TestBookmarks::modelFollowsSelectedFolder()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 folder = manager->addFolder(QStringLiteral("Model folder"),
                                             manager->toolbarFolderId());
    QVERIFY(folder > 0);

    // Every folder gets its own model, so the manager's right-hand list
    // always shows the selected folder (never the toolbar's rows).
    QVERIFY(manager->modelForFolder(folder) != manager->toolbarModel());
    QCOMPARE(manager->modelForFolder(folder)->folderId(), folder);
    QCOMPARE(manager->modelForFolder(folder)->rowCount(), 0);
    QCOMPARE(manager->modelForFolder(manager->toolbarFolderId()), manager->toolbarModel());
}

void TestBookmarks::removeFolderCascades()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 folder = manager->addFolder(QStringLiteral("Doomed"), manager->otherFolderId());
    const QUrl url(QStringLiteral("https://bookmarks.example/doomed"));
    const qint64 id = manager->addBookmark(url, QStringLiteral("Doomed page"), folder);
    QVERIFY(folder > 0 && id > 0);

    manager->remove(folder);
    QVERIFY(manager->bookmark(folder).isEmpty());
    QVERIFY(!manager->isBookmarked(url));

    // The fixed roots cannot be removed.
    manager->remove(manager->toolbarFolderId());
    QVERIFY(manager->toolbarFolderId() > 0);
}

void TestBookmarks::importNetscapeHtml()
{
    QTemporaryDir dir;
    QVERIFY(dir.isValid());
    const QString path = dir.filePath(QStringLiteral("bookmarks.html"));
    QFile file(path);
    QVERIFY(file.open(QIODevice::WriteOnly));
    file.write(R"(<!DOCTYPE NETSCAPE-Bookmark-file-1>
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
)");
    file.close();

    BookmarkManager *manager = BookmarkManager::instance();
    const int otherChildrenBeforeImport = manager->childCount(manager->otherFolderId());
    const int imported = manager->importHtml(QUrl::fromLocalFile(path));
    QCOMPARE(imported, 3);
    QVERIFY(manager->isBookmarked(QUrl(QStringLiteral("https://kde.org/"))));
    QVERIFY(manager->isBookmarked(QUrl(QStringLiteral("https://planet.kde.org/"))));
    QVERIFY(manager->isBookmarked(QUrl(QStringLiteral("https://bookmarks.example/emoji"))));

    // The import created "Imported" under "Other Bookmarks" with the tree.
    const QVariantList folders = manager->folders();
    qint64 importedFolder = -1;
    qint64 importedToolbar = -1;
    qint64 nestedFolder = -1;
    for (const QVariant &row : folders) {
        const QVariantMap map = row.toMap();
        const qint64 id = map.value(QStringLiteral("id")).toLongLong();
        const qint64 parent = map.value(QStringLiteral("parentId")).toLongLong();
        const QString title = map.value(QStringLiteral("title")).toString();
        if (title == QLatin1String("Imported"))
            importedFolder = id;
        else if (title == QLatin1String("Bookmarks Toolbar")
                 && parent == importedFolder)
            importedToolbar = id;
        else if (title == QLatin1String("Nested"))
            nestedFolder = id;
    }
    QVERIFY(importedFolder > 0);
    QVERIFY(importedToolbar > 0);
    QVERIFY(nestedFolder > 0);
    QCOMPARE(manager->bookmark(importedFolder).value(QStringLiteral("parentId")).toLongLong(),
             manager->otherFolderId());
    // "Imported" is appended, not stacked at position 0 of "Other Bookmarks".
    QCOMPARE(manager->bookmark(importedFolder).value(QStringLiteral("position")).toInt(),
             otherChildrenBeforeImport);
    QCOMPARE(manager->bookmark(nestedFolder).value(QStringLiteral("parentId")).toLongLong(),
             importedToolbar);

    // Numeric entities above U+FFFF are decoded into surrogate pairs.
    bool foundEmoji = false;
    const QVariantList importedContents = manager->folderContents(importedFolder);
    for (const QVariant &row : importedContents) {
        if (row.toMap().value(QStringLiteral("url")).toString()
            == QLatin1String("https://bookmarks.example/emoji")) {
            QCOMPARE(row.toMap().value(QStringLiteral("title")).toString(),
                     QStringLiteral("Emoji \U0001F600 \U0001F600"));
            foundEmoji = true;
        }
    }
    QVERIFY(foundEmoji);
}

int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("KDE-Test"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor-Bookmarks-Test"));

    // Never touch the real profile: the database lives in this temp dir.
    QTemporaryDir dataDir;
    if (!dataDir.isValid())
        return 1;
    qputenv("XDG_DATA_HOME", dataDir.path().toUtf8());
    qputenv("XDG_CONFIG_HOME", dataDir.path().toUtf8());
    qputenv("XDG_CACHE_HOME", dataDir.path().toUtf8());

    TestBookmarks test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_bookmarks.moc"
