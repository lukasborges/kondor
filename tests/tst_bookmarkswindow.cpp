#include <QGuiApplication>
#include <QQmlContext>
#include <QQmlEngine>
#include <QQmlExpression>
#include <QJSEngine>
#include <QQuickImageProvider>
#include <QQuickItem>
#include <QQuickStyle>
#include <QQuickWindow>
#include <QTemporaryDir>
#include <QTest>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include <functional>

#include "bookmarkmanager.h"
#include "database.h"
#include "faviconstore.h"
#include "profilemanager.h"
#include "tabmodel.h"

namespace {
// The window uses `image://kondor-favicon/` for bookmark rows; the real
// provider lives in the application, so the test accepts any request.
class EmptyImageProvider : public QQuickImageProvider
{
public:
    EmptyImageProvider()
        : QQuickImageProvider(QQuickImageProvider::Image)
    {
    }

    QImage requestImage(const QString &, QSize *size, const QSize &) override
    {
        QImage image(1, 1, QImage::Format_ARGB32);
        image.fill(Qt::transparent);
        if (size)
            *size = image.size();
        return image;
    }
};
}

// Drives the "Manage Bookmarks" window through the window's mouse-event path
// (QTest events are delivered by the platform like a physical mouse), covering
// the drag and drop gesture and the row clicks. The window is loaded from the
// source tree with the same `Kondor` types the app registers.
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

private:
    QQmlEngine m_engine;
    QQuickWindow *createWindow(TabModel *tabs, qint64 folderId);
    QQuickItem *rowAt(QQuickWindow *window, const QString &listId, int index);
    QPoint rowCenter(QQuickItem *row) const;
    bool previewShows(QQuickWindow *window, const QString &title) const;
    bool previewHidden(QQuickWindow *window) const;
    void drag(QQuickWindow *window, const QPoint &from, const QPoint &to,
              const std::function<void()> &duringDrag = {});
};

void TestBookmarksWindow::initTestCase()
{
    QVERIFY2(Database::instance()->isValid(), "the test database must open");

    // The same types the application's QML module exposes. The tests link the
    // real C++ classes instead of the compiled module.
    qmlRegisterType<TabModel>("Kondor", 1, 0, "TabModel");
    qmlRegisterSingletonType<BookmarkManager>("Kondor", 1, 0, "BookmarkManager",
                                              [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                  return BookmarkManager::instance();
                                              });
    qmlRegisterSingletonType<FaviconStore>("Kondor", 1, 0, "FaviconStore",
                                           [](QQmlEngine *, QJSEngine *) -> QObject * {
                                               return FaviconStore::instance();
                                           });
    m_engine.addImageProvider(QStringLiteral("kondor-favicon"), new EmptyImageProvider);
    qmlRegisterSingletonType<ProfileManager>("Kondor", 1, 0, "ProfileManager",
                                             [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                 return ProfileManager::instance();
                                             });
}

QQuickWindow *TestBookmarksWindow::createWindow(TabModel *tabs, qint64 folderId)
{
    // One engine for the whole test: QML singletons (and Kirigami's Units)
    // are registered per engine and must not be torn down between windows.
    QQmlComponent component(&m_engine,
                            QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR
                                                               "/BookmarksWindow.qml")));
    QObject *object = component.createWithInitialProperties({
        {QStringLiteral("tabModel"), QVariant::fromValue(tabs)},
        {QStringLiteral("selectedFolderId"), QVariant::fromValue(folderId)},
    });
    if (!object) {
        qWarning() << component.errors();
        return nullptr;
    }
    QQuickWindow *window = qobject_cast<QQuickWindow *>(object);
    if (!window) {
        delete object;
        return nullptr;
    }
    window->resize(820, 540);
    return window;
}

QQuickItem *TestBookmarksWindow::rowAt(QQuickWindow *window, const QString &listId, int index)
{
    QQmlExpression expression(qmlContext(window), window,
                              QStringLiteral("%1.itemAtIndex(%2)").arg(listId).arg(index));
    const QVariant value = expression.evaluate();
    if (expression.hasError())
        qWarning() << expression.error();
    return value.value<QQuickItem *>();
}

QPoint TestBookmarksWindow::rowCenter(QQuickItem *row) const
{
    return row->mapToScene(QPointF(row->width() / 2, row->height() / 2)).toPoint();
}

// The window-level preview is visible and carries the dragged item's title.
bool TestBookmarksWindow::previewShows(QQuickWindow *window, const QString &title) const
{
    QQmlExpression visible(qmlContext(window), window, QStringLiteral("dragProxy.visible"));
    const bool shown = visible.evaluate().toBool();
    QQuickItem *label = window->findChild<QQuickItem *>(QStringLiteral("dragPreviewTitle"));
    return shown && label && label->property("text").toString() == title;
}

bool TestBookmarksWindow::previewHidden(QQuickWindow *window) const
{
    QQmlExpression visible(qmlContext(window), window, QStringLiteral("dragProxy.visible"));
    return !visible.evaluate().toBool();
}

void TestBookmarksWindow::drag(QQuickWindow *window, const QPoint &from, const QPoint &to,
                               const std::function<void()> &duringDrag)
{
    QTest::mousePress(window, Qt::LeftButton, Qt::NoModifier, from);
    // A real pointer produces many moves; a single jump would not pass the
    // DragHandler threshold the same way.
    const int steps = 12;
    for (int i = 1; i <= steps; ++i) {
        const QPoint step = from + (to - from) * i / steps;
        QTest::mouseMove(window, step);
    }
    // Inspect the preview after the moves, with the button still pressed.
    if (duringDrag)
        duringDrag();
    QTest::mouseRelease(window, Qt::LeftButton, Qt::NoModifier, to);
    // Drag moves are delivered through queued events.
    QTest::qWait(100);
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
    QTRY_VERIFY((sourceRow = rowAt(window.data(), QStringLiteral("itemList"), 0)));
    QTRY_COMPARE(sourceRow->property("id").toLongLong(), id);

    // Index of the target folder in the flat tree model.
    const QVariantList folders = manager->folders();
    int targetIndex = -1;
    for (int i = 0; i < folders.size(); ++i) {
        if (folders.at(i).toMap().value(QStringLiteral("id")).toLongLong() == target)
            targetIndex = i;
    }
    QVERIFY(targetIndex >= 0);
    QQuickItem *targetRow = nullptr;
    QTRY_VERIFY((targetRow = rowAt(window.data(), QStringLiteral("folderList"), targetIndex)));

    bool previewShown = false;
    drag(window.data(), rowCenter(sourceRow), rowCenter(targetRow), [&]() {
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

    // Find the rows: the bookmark and the folder row in the right-hand list.
    QQuickItem *bookmarkRow = nullptr;
    QQuickItem *folderRow = nullptr;
    QTRY_VERIFY((bookmarkRow = rowAt(window.data(), QStringLiteral("itemList"),
                                     manager->modelForFolder(manager->otherFolderId())
                                         ->rowOf(id))));
    const int folderIndex = manager->modelForFolder(manager->otherFolderId())->rowOf(folder);
    QVERIFY(folderIndex >= 0);
    QTRY_VERIFY((folderRow = rowAt(window.data(), QStringLiteral("itemList"), folderIndex)));

    drag(window.data(), rowCenter(bookmarkRow), rowCenter(folderRow));

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
    QTRY_VERIFY((firstRow = rowAt(window.data(), QStringLiteral("itemList"), 0)));
    QTRY_VERIFY((secondRow = rowAt(window.data(), QStringLiteral("itemList"), 1)));
    QTRY_COMPARE(secondRow->property("id").toLongLong(), second);

    // Drop in the top band of the first row: insert above it.
    const QPoint from = rowCenter(secondRow);
    const QPoint to = firstRow->mapToScene(QPointF(firstRow->width() / 2, 2)).toPoint();
    bool previewShown = false;
    drag(window.data(), from, QPoint(to.x(), to.y() + 1), [&]() {
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
    QTRY_VERIFY((bookmarkRow = rowAt(window.data(), QStringLiteral("itemList"), 0)));

    // Right click still selects the row and opens its menu (no navigation).
    QTest::mouseClick(window.data(), Qt::RightButton, Qt::NoModifier, rowCenter(bookmarkRow));
    QCOMPARE(window->property("selectedItemId").toLongLong(), id);
    {
        QQmlExpression menu(qmlContext(window.data()), window.data(),
                            QStringLiteral("itemContextMenu.visible"));
        QCOMPARE(menu.evaluate().toBool(), true);
        QQmlExpression close(qmlContext(window.data()), window.data(),
                             QStringLiteral("itemContextMenu.close()"));
        close.evaluate();
    }

    // Clicks on the tree still reach the delegates below the tree DropArea.
    const QVariantList folders = manager->folders();
    int otherIndex = -1;
    for (int i = 0; i < folders.size(); ++i) {
        if (folders.at(i).toMap().value(QStringLiteral("id")).toLongLong() == other)
            otherIndex = i;
    }
    QVERIFY(otherIndex >= 0);
    QQuickItem *otherRow = nullptr;
    QTRY_VERIFY((otherRow = rowAt(window.data(), QStringLiteral("folderList"), otherIndex)));

    QTest::mouseClick(window.data(), Qt::LeftButton, Qt::NoModifier, rowCenter(otherRow));
    QCOMPARE(window->property("selectedFolderId").toLongLong(), other);
    QCOMPARE(window->property("selectedItemId").toLongLong(), qint64(-1));
}

void TestBookmarksWindow::deleteDialogHasTwoButtons()
{
    TabModel model;
    QScopedPointer<QQuickWindow> window(createWindow(&model, BookmarkManager::instance()->otherFolderId()));
    QVERIFY(window);
    QQmlExpression type(qmlContext(window.data()), window.data(),
                        QStringLiteral("deleteDialog.footer.contentChildren.length"));
    QCOMPARE(type.evaluate().toInt(), 2);
    QQmlExpression texts(qmlContext(window.data()), window.data(),
                         QStringLiteral("deleteDialog.footer.contentChildren.map(b => b.text).join('|')"));
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
    QQmlExpression open(qmlContext(window.data()), window.data(),
                        QStringLiteral("deleteDialog.targetId = %1; deleteDialog.accept()").arg(folder));
    open.evaluate();
    QVERIFY(!manager->bookmark(folder).value(QStringLiteral("id")).toLongLong());
}

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();

    // Never touch the real profile: the database and settings live here.
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
