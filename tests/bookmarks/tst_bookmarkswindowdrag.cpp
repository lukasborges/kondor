#include "bookmarkswindowharness.h"
#include "core/database.h"

class TestBookmarksWindowDrag : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void dragIntoTreeFolder();
    void dragOntoFolderRow();
    void dragBetweenRows();
    void clicksStillSelect();

private:
    void verifyRightClickSelects(QQuickWindow *window, QQuickItem *row, qint64 id);
    void verifyLeftClickSelectsFolder(QQuickWindow *window, qint64 folderId);

    QQmlEngine m_engine;
};

void TestBookmarksWindowDrag::initTestCase()
{
    QVERIFY2(Database::instance()->isValid(), "the test database must open");
    registerKondorTypes(m_engine);
}

void TestBookmarksWindowDrag::dragIntoTreeFolder()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 source = manager->addFolder(QStringLiteral("Drag source"), manager->toolbarFolderId());
    const qint64 target = manager->addFolder(QStringLiteral("Drag target"), manager->toolbarFolderId());
    QVERIFY(source > 0 && target > 0);
    const qint64 id = addBookmarkTo(source, QStringLiteral("Tree drag"), QStringLiteral("https://drag.example/tree"));
    QVERIFY(id > 0);
    BookmarksWindowFixture fixture(m_engine, source);
    QVERIFY(fixture.window() && fixture.show());
    QQuickItem *sourceRow = waitForRow(fixture.window(), "itemList", 0);
    QVERIFY(sourceRow);
    QTRY_COMPARE(sourceRow->property("id").toLongLong(), id);
    QVERIFY(folderRowOf(target) >= 0);
    QQuickItem *targetRow = waitForRow(fixture.window(), "folderList", folderRowOf(target));
    QVERIFY(targetRow);
    const bool previewShown = dragShowingPreview(fixture.window(), {rowCenter(sourceRow), rowCenter(targetRow)}, QStringLiteral("Tree drag"));
    QVERIFY(previewShown);
    QVERIFY(previewHidden(fixture.window()));
    QCOMPARE(parentIdOf(id), target);
}

void TestBookmarksWindowDrag::dragOntoFolderRow()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 other = manager->otherFolderId();
    const qint64 folder = manager->addFolder(QStringLiteral("Row target"), other);
    QVERIFY(folder > 0);
    const qint64 id = addBookmarkTo(other, QStringLiteral("Row drag"), QStringLiteral("https://drag.example/row"));
    QVERIFY(id > 0);
    BookmarksWindowFixture fixture(m_engine, other);
    QVERIFY(fixture.window() && fixture.show());
    BookmarkModel *items = manager->modelForFolder(other);
    QVERIFY(items->rowOf(folder) >= 0);
    QQuickItem *bookmarkRow = waitForRow(fixture.window(), "itemList", items->rowOf(id));
    QQuickItem *folderRow = waitForRow(fixture.window(), "itemList", items->rowOf(folder));
    QVERIFY(bookmarkRow && folderRow);
    dragWithButtonDown(fixture.window(), rowCenter(bookmarkRow), rowCenter(folderRow));
    QCOMPARE(parentIdOf(id), folder);
}

void TestBookmarksWindowDrag::dragBetweenRows()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 folder = manager->addFolder(QStringLiteral("Reorder folder"), manager->toolbarFolderId());
    QVERIFY(folder > 0);
    const qint64 first = addBookmarkTo(folder, QStringLiteral("First"), QStringLiteral("https://drag.example/first"));
    const qint64 second = addBookmarkTo(folder, QStringLiteral("Second"), QStringLiteral("https://drag.example/second"));
    QVERIFY(first > 0 && second > 0);
    BookmarksWindowFixture fixture(m_engine, folder);
    QVERIFY(fixture.window() && fixture.show());
    QQuickItem *firstRow = waitForRow(fixture.window(), "itemList", 0);
    QQuickItem *secondRow = waitForRow(fixture.window(), "itemList", 1);
    QVERIFY(firstRow && secondRow);
    QTRY_COMPARE(secondRow->property("id").toLongLong(), second);
    const bool previewShown = dragShowingPreview(fixture.window(), {rowCenter(secondRow), justInsideTopEdge(firstRow)}, QStringLiteral("Second"));
    QVERIFY(previewShown);
    QVERIFY(previewHidden(fixture.window()));
    const QVariantList contents = manager->folderContents(folder);
    QCOMPARE(contents.size(), 2);
    QCOMPARE(contents.first().toMap().value(QStringLiteral("id")).toLongLong(), second);
}

void TestBookmarksWindowDrag::verifyRightClickSelects(QQuickWindow *window, QQuickItem *row, qint64 id)
{
    QTest::mouseClick(window, Qt::RightButton, Qt::NoModifier, rowCenter(row));
    QCOMPARE(window->property("selectedItemId").toLongLong(), id);
    QObject *menu = childNamed(window, "itemContextMenu");
    QCOMPARE(menu->property("visible").toBool(), true);
    QMetaObject::invokeMethod(menu, "close");
}

void TestBookmarksWindowDrag::verifyLeftClickSelectsFolder(QQuickWindow *window, qint64 folderId)
{
    QVERIFY(folderRowOf(folderId) >= 0);
    QQuickItem *row = waitForRow(window, "folderList", folderRowOf(folderId));
    QVERIFY(row);
    QTest::mouseClick(window, Qt::LeftButton, Qt::NoModifier, rowCenter(row));
    QCOMPARE(window->property("selectedFolderId").toLongLong(), folderId);
    QCOMPARE(window->property("selectedItemId").toLongLong(), qint64(-1));
}

void TestBookmarksWindowDrag::clicksStillSelect()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 folder = manager->addFolder(QStringLiteral("Click folder"), manager->toolbarFolderId());
    const qint64 other = manager->addFolder(QStringLiteral("Click other"), manager->toolbarFolderId());
    QVERIFY(folder > 0 && other > 0);
    const qint64 id = addBookmarkTo(folder, QStringLiteral("Click bookmark"), QStringLiteral("https://drag.example/click"));
    QVERIFY(id > 0);
    BookmarksWindowFixture fixture(m_engine, folder);
    QVERIFY(fixture.window() && fixture.show());
    QQuickItem *bookmarkRow = waitForRow(fixture.window(), "itemList", 0);
    QVERIFY(bookmarkRow);
    verifyRightClickSelects(fixture.window(), bookmarkRow, id);
    verifyLeftClickSelectsFolder(fixture.window(), other);
}

int runTestBookmarksWindowDrag(int argc, char *argv[])
{
    TestBookmarksWindowDrag test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_bookmarkswindowdrag.moc"
