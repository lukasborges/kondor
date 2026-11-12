#include <QGuiApplication>
#include <QQmlContext>
#include <QQmlExpression>
#include <QQuickStyle>
#include <QTemporaryDir>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "bookmarkswindowharness.h"
#include "common/isolatedhome.h"
#include "core/database.h"

class TestBookmarksWindow : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void deleteDialogHasTwoButtons();
    void acceptingDeleteDialogRemovesFolder();
    void moveDownReordersTheSelectedItem();
    void returnOnAFolderRowOpensThatFolder();
    void searchFiltersTheSelectedFolder();
    void moveToMenuSkipsParentAndOwnSubtree();

private:
    QQmlEngine m_engine;
};

void TestBookmarksWindow::initTestCase()
{
    QVERIFY2(Database::instance()->isValid(), "the test database must open");
    registerKondorTypes(m_engine);
}

void TestBookmarksWindow::deleteDialogHasTwoButtons()
{
    BookmarksWindowFixture fixture(m_engine, BookmarkManager::instance()->otherFolderId());
    QVERIFY(fixture.window());
    QObject *dialog = childNamed(fixture.window(), "deleteDialog");
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
    BookmarksWindowFixture fixture(m_engine, folder);
    QVERIFY(fixture.window());
    QObject *dialog = childNamed(fixture.window(), "deleteDialog");
    dialog->setProperty("targetId", folder);
    QMetaObject::invokeMethod(dialog, "accept");
    QVERIFY(!manager->bookmark(folder).value(QStringLiteral("id")).toLongLong());
}

void TestBookmarksWindow::moveDownReordersTheSelectedItem()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 folder = manager->addFolder(QStringLiteral("Move down"), manager->toolbarFolderId());
    const qint64 first = addBookmarkTo(folder, QStringLiteral("One"), QStringLiteral("https://down.example/1"));
    const qint64 second = addBookmarkTo(folder, QStringLiteral("Two"), QStringLiteral("https://down.example/2"));
    BookmarksWindowFixture fixture(m_engine, folder);
    QVERIFY(fixture.window() && fixture.show());
    QQuickItem *row = waitForRow(fixture.window(), "itemList", 0);
    QVERIFY(row);
    QTest::mouseClick(fixture.window(), Qt::LeftButton, Qt::NoModifier, rowCenter(row));
    QMetaObject::invokeMethod(childNamed(fixture.window(), "moveDownButton"), "click");
    QCOMPARE(manager->folderContents(folder).first().toMap().value(QStringLiteral("id")).toLongLong(), second);
    QCOMPARE(fixture.window()->property("selectedItemId").toLongLong(), first);
    QTRY_COMPARE(childNamed(fixture.window(), "itemList")->property("currentIndex").toInt(), 1);
}

void TestBookmarksWindow::returnOnAFolderRowOpensThatFolder()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 parent = manager->addFolder(QStringLiteral("Return parent"), manager->toolbarFolderId());
    addBookmarkTo(parent, QStringLiteral("Plain"), QStringLiteral("https://return.example"));
    const qint64 child = manager->addFolder(QStringLiteral("Return child"), parent);
    BookmarksWindowFixture fixture(m_engine, parent);
    QVERIFY(fixture.window() && fixture.show());
    auto *list = qobject_cast<QQuickItem *>(childNamed(fixture.window(), "itemList"));
    QVERIFY(list);
    list->forceActiveFocus();
    list->setProperty("currentIndex", manager->modelForFolder(parent)->rowOf(child));
    QTest::keyClick(fixture.window(), Qt::Key_Return);
    QCOMPARE(fixture.window()->property("selectedFolderId").toLongLong(), child);
}

void TestBookmarksWindow::searchFiltersTheSelectedFolder()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 first = manager->addFolder(QStringLiteral("Search first"), manager->toolbarFolderId());
    const qint64 second = manager->addFolder(QStringLiteral("Search second"), manager->toolbarFolderId());
    addBookmarkTo(first, QStringLiteral("Alpha"), QStringLiteral("https://search.example/a"));
    addBookmarkTo(first, QStringLiteral("Beta"), QStringLiteral("https://search.example/b"));
    BookmarksWindowFixture fixture(m_engine, first);
    QVERIFY(fixture.window());
    childNamed(fixture.window(), "bookmarkSearchField")->setProperty("text", QStringLiteral("alpha"));
    QTRY_COMPARE(manager->modelForFolder(first)->count(), 1);
    fixture.window()->setProperty("selectedFolderId", QVariant::fromValue(second));
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
    BookmarksWindowFixture fixture(m_engine, parent);
    QVERIFY(fixture.window() && fixture.show());
    QQuickItem *row = waitForRow(fixture.window(), "itemList", manager->modelForFolder(parent)->rowOf(moved));
    QVERIFY(row);
    QTest::mouseClick(fixture.window(), Qt::RightButton, Qt::NoModifier, rowCenter(row));
    const QStringList titles = menuTitles(childNamed(fixture.window(), "moveToMenu"));
    QVERIFY(titles.contains(QStringLiteral("MoveS")));
    for (const QString &skipped : { QStringLiteral("MoveP"), QStringLiteral("MoveC"), QStringLiteral("MoveG") })
        QVERIFY2(!titles.contains(skipped), qPrintable(skipped));
}

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();
    QTemporaryDir home;
    if (!useIsolatedHome(home))
        return 1;
    QGuiApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("KDE-Test"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor-BookmarksWindow-Test"));
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));
    const int dragFailures = runTestBookmarksWindowDrag(argc, argv);
    TestBookmarksWindow test;
    return dragFailures + QTest::qExec(&test, argc, argv);
}

#include "tst_bookmarkswindow.moc"
