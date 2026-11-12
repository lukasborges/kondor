#include <QGuiApplication>
#include <QQmlContext>
#include <QQmlExpression>
#include <QQuickStyle>
#include <QTemporaryDir>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "bookmarkswindowharness.h"
#include "core/database.h"

class TestBookmarksWindow : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void dragIntoTreeFolder();
    void dragOntoFolderRow();
    void dragBetweenRows();
    void clicksStillSelect();
    void deleteDialogHasTwoButtons();
    void acceptingDeleteDialogRemovesFolder();
    void moveDownReordersTheSelectedItem();
    void returnOnAFolderRowOpensThatFolder();
    void searchFiltersTheSelectedFolder();
    void moveToMenuSkipsParentAndOwnSubtree();

private:
    QQmlEngine m_engine;
    QQuickWindow *createWindow(TabModel *tabs, qint64 folderId)
    {
        return createBookmarksWindow(m_engine, tabs, folderId);
    }
    bool previewShows(QQuickWindow *window, const QString &title) const;
    bool previewHidden(QQuickWindow *window) const;
};

void TestBookmarksWindow::initTestCase()
{
    QVERIFY2(Database::instance()->isValid(), "the test database must open");
    registerKondorTypes(m_engine);
}

bool TestBookmarksWindow::previewShows(QQuickWindow *window, const QString &title) const
{
    const bool shown = childNamed(window, "dragProxy")->property("visible").toBool();
    QObject *label = childNamed(window, "dragPreviewTitle");
    return shown && label && label->property("text").toString() == title;
}

bool TestBookmarksWindow::previewHidden(QQuickWindow *window) const
{
    return !childNamed(window, "dragProxy")->property("visible").toBool();
}

void TestBookmarksWindow::dragIntoTreeFolder()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 toolbar = manager->toolbarFolderId();
    const qint64 source = manager->addFolder(QStringLiteral("Drag source"), toolbar);
    const qint64 target = manager->addFolder(QStringLiteral("Drag target"), toolbar);
    QVERIFY(source > 0 && target > 0);
    const qint64 id = manager->addBookmark(QUrl(QStringLiteral("https://drag.example/tree")),
                                           QStringLiteral("Tree drag"), source);
    QVERIFY(id > 0);

    TabModel model;
    QScopedPointer<QQuickWindow> window(createWindow(&model, source));
    QVERIFY(window);
    window->show();
    QVERIFY(QTest::qWaitForWindowExposed(window.data()));

    QQuickItem *sourceRow = nullptr;
    QTRY_VERIFY((sourceRow = rowAt(window.data(), "itemList", 0)));
    QTRY_COMPARE(sourceRow->property("id").toLongLong(), id);

    const int targetIndex = folderRowOf(target);
    QVERIFY(targetIndex >= 0);
    QQuickItem *targetRow = nullptr;
    QTRY_VERIFY((targetRow = rowAt(window.data(), "folderList", targetIndex)));

    bool previewShown = false;
    dragWithButtonDown(window.data(), rowCenter(sourceRow), rowCenter(targetRow), [&]() {
        previewShown = previewShows(window.data(), QStringLiteral("Tree drag"));
    });
    QVERIFY(previewShown);
    QVERIFY(previewHidden(window.data()));

    QCOMPARE(manager->bookmark(id).value(QStringLiteral("parentId")).toLongLong(), target);
}

void TestBookmarksWindow::dragOntoFolderRow()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 folder = manager->addFolder(QStringLiteral("Row target"),
                                             manager->otherFolderId());
    QVERIFY(folder > 0);
    const qint64 id = manager->addBookmark(QUrl(QStringLiteral("https://drag.example/row")),
                                           QStringLiteral("Row drag"),
                                           manager->otherFolderId());
    QVERIFY(id > 0);

    TabModel model;
    QScopedPointer<QQuickWindow> window(createWindow(&model, manager->otherFolderId()));
    QVERIFY(window);
    window->show();
    QVERIFY(QTest::qWaitForWindowExposed(window.data()));

    QQuickItem *bookmarkRow = nullptr;
    QQuickItem *folderRow = nullptr;
    QTRY_VERIFY((bookmarkRow = rowAt(window.data(), "itemList",
                                     manager->modelForFolder(manager->otherFolderId())
                                         ->rowOf(id))));
    const int folderIndex = manager->modelForFolder(manager->otherFolderId())->rowOf(folder);
    QVERIFY(folderIndex >= 0);
    QTRY_VERIFY((folderRow = rowAt(window.data(), "itemList", folderIndex)));

    dragWithButtonDown(window.data(), rowCenter(bookmarkRow), rowCenter(folderRow));

    QCOMPARE(manager->bookmark(id).value(QStringLiteral("parentId")).toLongLong(), folder);
}

void TestBookmarksWindow::dragBetweenRows()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 folder = manager->addFolder(QStringLiteral("Reorder folder"),
                                             manager->toolbarFolderId());
    QVERIFY(folder > 0);
    const qint64 first = manager->addBookmark(QUrl(QStringLiteral("https://drag.example/first")),
                                              QStringLiteral("First"),
                                              folder);
    const qint64 second = manager->addBookmark(QUrl(QStringLiteral("https://drag.example/second")),
                                               QStringLiteral("Second"),
                                               folder);
    QVERIFY(first > 0 && second > 0);

    TabModel model;
    QScopedPointer<QQuickWindow> window(createWindow(&model, folder));
    QVERIFY(window);
    window->show();
    QVERIFY(QTest::qWaitForWindowExposed(window.data()));

    QQuickItem *firstRow = nullptr;
    QQuickItem *secondRow = nullptr;
    QTRY_VERIFY((firstRow = rowAt(window.data(), "itemList", 0)));
    QTRY_VERIFY((secondRow = rowAt(window.data(), "itemList", 1)));
    QTRY_COMPARE(secondRow->property("id").toLongLong(), second);

    const QPoint from = rowCenter(secondRow);
    const QPoint to = firstRow->mapToScene(QPointF(firstRow->width() / 2, 2)).toPoint();
    bool previewShown = false;
    dragWithButtonDown(window.data(), from, QPoint(to.x(), to.y() + 1), [&]() {
        previewShown = previewShows(window.data(), QStringLiteral("Second"));
    });
    QVERIFY(previewShown);
    QVERIFY(previewHidden(window.data()));

    const QVariantList contents = manager->folderContents(folder);
    QCOMPARE(contents.size(), 2);
    QCOMPARE(contents.first().toMap().value(QStringLiteral("id")).toLongLong(), second);
}

void TestBookmarksWindow::clicksStillSelect()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 folder = manager->addFolder(QStringLiteral("Click folder"),
                                             manager->toolbarFolderId());
    const qint64 other = manager->addFolder(QStringLiteral("Click other"),
                                            manager->toolbarFolderId());
    QVERIFY(folder > 0 && other > 0);
    const qint64 id = manager->addBookmark(QUrl(QStringLiteral("https://drag.example/click")),
                                           QStringLiteral("Click bookmark"), folder);
    QVERIFY(id > 0);

    TabModel model;
    QScopedPointer<QQuickWindow> window(createWindow(&model, folder));
    QVERIFY(window);
    window->show();
    QVERIFY(QTest::qWaitForWindowExposed(window.data()));

    QQuickItem *bookmarkRow = nullptr;
    QTRY_VERIFY((bookmarkRow = rowAt(window.data(), "itemList", 0)));

    QTest::mouseClick(window.data(), Qt::RightButton, Qt::NoModifier, rowCenter(bookmarkRow));
    QCOMPARE(window->property("selectedItemId").toLongLong(), id);
    QObject *menu = childNamed(window.data(), "itemContextMenu");
    QCOMPARE(menu->property("visible").toBool(), true);
    QMetaObject::invokeMethod(menu, "close");

    const int otherIndex = folderRowOf(other);
    QVERIFY(otherIndex >= 0);
    QQuickItem *otherRow = nullptr;
    QTRY_VERIFY((otherRow = rowAt(window.data(), "folderList", otherIndex)));

    QTest::mouseClick(window.data(), Qt::LeftButton, Qt::NoModifier, rowCenter(otherRow));
    QCOMPARE(window->property("selectedFolderId").toLongLong(), other);
    QCOMPARE(window->property("selectedItemId").toLongLong(), qint64(-1));
}

void TestBookmarksWindow::deleteDialogHasTwoButtons()
{
    TabModel model;
    QScopedPointer<QQuickWindow> window(createWindow(&model, BookmarkManager::instance()->otherFolderId()));
    QVERIFY(window);
    QObject *dialog = childNamed(window.data(), "deleteDialog");
    QQmlExpression count(qmlContext(dialog), dialog, QStringLiteral("footer.contentChildren.length"));
    QCOMPARE(count.evaluate().toInt(), 2);
    QQmlExpression texts(qmlContext(dialog), dialog,
                         QStringLiteral("footer.contentChildren.map(b => b.text).join('|')"));
    QCOMPARE(texts.evaluate().toString(), QStringLiteral("Delete|Cancel"));
}

void TestBookmarksWindow::acceptingDeleteDialogRemovesFolder()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 folder = manager->addFolder(QStringLiteral("Doomed"), manager->otherFolderId());
    QVERIFY(folder > 0);
    TabModel model;
    QScopedPointer<QQuickWindow> window(createWindow(&model, folder));
    QVERIFY(window);
    QObject *dialog = childNamed(window.data(), "deleteDialog");
    dialog->setProperty("targetId", folder);
    QMetaObject::invokeMethod(dialog, "accept");
    QVERIFY(!manager->bookmark(folder).value(QStringLiteral("id")).toLongLong());
}

void TestBookmarksWindow::moveDownReordersTheSelectedItem()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 folder = manager->addFolder(QStringLiteral("Move down"), manager->toolbarFolderId());
    const qint64 first = manager->addBookmark(QUrl(QStringLiteral("https://down.example/1")), QStringLiteral("One"), folder);
    const qint64 second = manager->addBookmark(QUrl(QStringLiteral("https://down.example/2")), QStringLiteral("Two"), folder);
    TabModel model;
    QScopedPointer<QQuickWindow> window(createWindow(&model, folder));
    QVERIFY(window);
    window->show();
    QVERIFY(QTest::qWaitForWindowExposed(window.data()));
    QQuickItem *row = nullptr;
    QTRY_VERIFY((row = rowAt(window.data(), "itemList", 0)));
    QTest::mouseClick(window.data(), Qt::LeftButton, Qt::NoModifier, rowCenter(row));
    QMetaObject::invokeMethod(childNamed(window.data(), "moveDownButton"), "click");
    QCOMPARE(manager->folderContents(folder).first().toMap().value(QStringLiteral("id")).toLongLong(), second);
    QCOMPARE(window->property("selectedItemId").toLongLong(), first);
    QTRY_COMPARE(childNamed(window.data(), "itemList")->property("currentIndex").toInt(), 1);
}

void TestBookmarksWindow::returnOnAFolderRowOpensThatFolder()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 parent = manager->addFolder(QStringLiteral("Return parent"), manager->toolbarFolderId());
    manager->addBookmark(QUrl(QStringLiteral("https://return.example")), QStringLiteral("Plain"), parent);
    const qint64 child = manager->addFolder(QStringLiteral("Return child"), parent);
    TabModel model;
    QScopedPointer<QQuickWindow> window(createWindow(&model, parent));
    QVERIFY(window);
    window->show();
    QVERIFY(QTest::qWaitForWindowExposed(window.data()));
    auto *list = qobject_cast<QQuickItem *>(childNamed(window.data(), "itemList"));
    QVERIFY(list);
    list->forceActiveFocus();
    list->setProperty("currentIndex", manager->modelForFolder(parent)->rowOf(child));
    QTest::keyClick(window.data(), Qt::Key_Return);
    QCOMPARE(window->property("selectedFolderId").toLongLong(), child);
}

void TestBookmarksWindow::searchFiltersTheSelectedFolder()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 first = manager->addFolder(QStringLiteral("Search first"), manager->toolbarFolderId());
    const qint64 second = manager->addFolder(QStringLiteral("Search second"), manager->toolbarFolderId());
    manager->addBookmark(QUrl(QStringLiteral("https://search.example/a")), QStringLiteral("Alpha"), first);
    manager->addBookmark(QUrl(QStringLiteral("https://search.example/b")), QStringLiteral("Beta"), first);
    TabModel model;
    QScopedPointer<QQuickWindow> window(createWindow(&model, first));
    QVERIFY(window);
    childNamed(window.data(), "bookmarkSearchField")->setProperty("text", QStringLiteral("alpha"));
    QTRY_COMPARE(manager->modelForFolder(first)->count(), 1);
    window->setProperty("selectedFolderId", QVariant::fromValue(second));
    QCOMPARE(manager->modelForFolder(first)->filter(), QString());
    QCOMPARE(manager->modelForFolder(second)->filter(), QStringLiteral("alpha"));
}

void TestBookmarksWindow::moveToMenuSkipsParentAndOwnSubtree()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 parent = manager->addFolder(QStringLiteral("MoveP"), manager->toolbarFolderId());
    const qint64 moved = manager->addFolder(QStringLiteral("MoveC"), parent);
    manager->addFolder(QStringLiteral("MoveG"), moved);
    manager->addFolder(QStringLiteral("MoveS"), parent);
    TabModel model;
    QScopedPointer<QQuickWindow> window(createWindow(&model, parent));
    QVERIFY(window);
    window->show();
    QVERIFY(QTest::qWaitForWindowExposed(window.data()));
    QQuickItem *row = nullptr;
    QTRY_VERIFY((row = rowAt(window.data(), "itemList", manager->modelForFolder(parent)->rowOf(moved))));
    QTest::mouseClick(window.data(), Qt::RightButton, Qt::NoModifier, rowCenter(row));
    const QStringList titles = menuTitles(childNamed(window.data(), "moveToMenu"));
    QVERIFY(titles.contains(QStringLiteral("MoveS")));
    for (const QString &skipped : { QStringLiteral("MoveP"), QStringLiteral("MoveC"), QStringLiteral("MoveG") })
        QVERIFY2(!titles.contains(skipped), qPrintable(skipped));
}

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();

    QTemporaryDir home;
    if (!home.isValid())
        return 1;
    qputenv("XDG_DATA_HOME", home.path().toUtf8());
    qputenv("XDG_CONFIG_HOME", home.path().toUtf8());
    qputenv("XDG_CACHE_HOME", home.path().toUtf8());

    QGuiApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("KDE-Test"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor-BookmarksWindow-Test"));
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));

    TestBookmarksWindow test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_bookmarkswindow.moc"
