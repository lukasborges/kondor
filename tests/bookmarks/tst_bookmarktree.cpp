#include "bookmarks/bookmarkmanager.h"
#include "bookmarks/bookmarkmodel.h"
#include "bookmarktreeharness.h"
#include "bookmarksprofileharness.h"
#include "core/database/database.h"

class TestBookmarkTree : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void rootFolders();
    void addAndFindBookmarks();
    void searchBookmarksFindsTitlesAndUrls();
    void moveBetweenFolders();
    void sortingInsideAFolderMovesTheSecondItemAboveTheFirst();
    void modelReportsTheMovedRow();
    void folderCannotMoveIntoItself();
    void moveIntoAnotherFolderAtEnd();
    void refuseMovingFolderIntoChild();
    void modelFollowsSelectedFolder();
    void removeFolderCascades();
};

void TestBookmarkTree::initTestCase()
{
    QVERIFY2(Database::instance()->isValid(), "the test database must open");
}

void TestBookmarkTree::rootFolders()
{
    BookmarkManager *manager = BookmarkManager::instance();
    QVERIFY(manager->toolbarFolderId() > 0);
    QVERIFY(manager->otherFolderId() > 0);
    QVERIFY(manager->toolbarFolderId() != manager->otherFolderId());
    QCOMPARE(manager->toolbarModel()->folderId(), manager->toolbarFolderId());
}

void TestBookmarkTree::addAndFindBookmarks()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const QUrl url(QStringLiteral("https://bookmarks.example/page"));
    QVERIFY(!manager->isBookmarked(url));
    const qint64 other = manager->otherFolderId();
    const qint64 first = manager->addBookmark(url, QStringLiteral("Page"), other);
    QVERIFY(first > 0);
    QVERIFY(manager->isBookmarked(url));
    QCOMPARE(manager->bookmarkIdFor(url), first);
    verifySameUrlInToolbarGetsItsOwnId(url, first);
    const QVariantMap info = manager->bookmark(first);
    QCOMPARE(info.value(QStringLiteral("parentId")).toLongLong(), other);
    QCOMPARE(info.value(QStringLiteral("title")).toString(), QStringLiteral("Page"));
}

void TestBookmarkTree::searchBookmarksFindsTitlesAndUrls()
{
    addSearchFixture();
    verifySearchByTitle();
    verifySearchByUrl();
    verifySearchSkipsFoldersAndHonoursLimit();
}

void TestBookmarkTree::moveBetweenFolders()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 folder = addFolderInOther(QStringLiteral("Moved"));
    QVERIFY(folder > 0);
    const qint64 id = addPage(manager->otherFolderId(), QStringLiteral("Move me"), QStringLiteral("move"));
    QVERIFY(id > 0);
    manager->move(id, folder, -1);
    QCOMPARE(parentOf(id), folder);
    QCOMPARE(manager->childCount(folder), 1);
}

void TestBookmarkTree::sortingInsideAFolderMovesTheSecondItemAboveTheFirst()
{
    const ReorderedFolder reordered = reorderedFolder();
    QVERIFY(reordered.folder > 0 && reordered.movedToTop > 0 && reordered.pushedDown > 0);
    const QVariantList contents = BookmarkManager::instance()->folderContents(reordered.folder);
    QCOMPARE(contents.size(), 2);
    QCOMPARE(contents.first().toMap().value(QStringLiteral("id")).toLongLong(), reordered.movedToTop);
}

void TestBookmarkTree::modelReportsTheMovedRow()
{
    const ReorderedFolder reordered = reorderedFolder();
    BookmarkModel *model = BookmarkManager::instance()->modelForFolder(reordered.folder);
    QCOMPARE(model->rowOf(reordered.movedToTop), 0);
    QCOMPARE(model->idAt(0), reordered.movedToTop);
    QCOMPARE(model->rowOf(reordered.pushedDown), 1);
    QCOMPARE(model->rowOf(999999), -1);
}

void TestBookmarkTree::folderCannotMoveIntoItself()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 folder = addFolderInOther(QStringLiteral("Self"));
    QVERIFY(folder > 0);
    manager->move(folder, folder, 0);
    QCOMPARE(parentOf(folder), manager->otherFolderId());
}

void TestBookmarkTree::moveIntoAnotherFolderAtEnd()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const FolderWithPage target = addFolderWithPage(QStringLiteral("Move target"), QStringLiteral("End A"), QStringLiteral("end-a"));
    const FolderWithPage source = addFolderWithPage(QStringLiteral("Move source"), QStringLiteral("End B"), QStringLiteral("end-b"));
    QVERIFY(target.folder > 0 && target.page > 0);
    QVERIFY(source.folder > 0 && source.page > 0);
    manager->move(source.page, target.folder, manager->childCount(target.folder));
    QCOMPARE(parentOf(source.page), target.folder);
    QCOMPARE(manager->bookmark(source.page).value(QStringLiteral("position")).toInt(), 1);
    QCOMPARE(manager->childCount(source.folder), 0);
    BookmarkModel *model = manager->modelForFolder(target.folder);
    QCOMPARE(model->rowOf(target.page), 0);
    QCOMPARE(model->rowOf(source.page), 1);
}

void TestBookmarkTree::refuseMovingFolderIntoChild()
{
    const qint64 parent = addFolderInOther(QStringLiteral("Cycle parent"));
    QVERIFY(parent > 0);
    const qint64 child = BookmarkManager::instance()->addFolder(QStringLiteral("Cycle child"), parent);
    QVERIFY(child > 0);
    const qint64 grandchild = BookmarkManager::instance()->addFolder(QStringLiteral("Cycle grandchild"), child);
    QVERIFY(grandchild > 0);
    BookmarkManager::instance()->move(parent, grandchild, 0);
    QCOMPARE(parentOf(parent), BookmarkManager::instance()->otherFolderId());
    QCOMPARE(parentOf(child), parent);
    QCOMPARE(parentOf(grandchild), child);
}

void TestBookmarkTree::modelFollowsSelectedFolder()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 folder = manager->addFolder(QStringLiteral("Model folder"), manager->toolbarFolderId());
    QVERIFY(folder > 0);
    QVERIFY(manager->modelForFolder(folder) != manager->toolbarModel());
    QCOMPARE(manager->modelForFolder(folder)->folderId(), folder);
    QCOMPARE(manager->modelForFolder(folder)->rowCount(), 0);
    QCOMPARE(manager->modelForFolder(manager->toolbarFolderId()), manager->toolbarModel());
}

void TestBookmarkTree::removeFolderCascades()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const FolderWithPage doomed = addFolderWithPage(QStringLiteral("Doomed"), QStringLiteral("Doomed page"), QStringLiteral("doomed"));
    QVERIFY(doomed.folder > 0 && doomed.page > 0);
    manager->remove(doomed.folder);
    QVERIFY(manager->bookmark(doomed.folder).isEmpty());
    QVERIFY(!manager->isBookmarked(QUrl(QStringLiteral("https://bookmarks.example/doomed"))));
    manager->remove(manager->toolbarFolderId());
    QVERIFY(manager->toolbarFolderId() > 0);
}

int runTestBookmarkTree(int argc, char *argv[])
{
    TestBookmarkTree test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_bookmarktree.moc"
