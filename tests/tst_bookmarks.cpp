#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QProcess>
#include <QSqlDatabase>
#include <QSqlQuery>
#include <QStandardPaths>
#include <QTemporaryDir>
#include <QTest>
#include <QVariantMap>

#include "bookmarkmanager.h"
#include "bookmarkmodel.h"
#include "database.h"

namespace {
QString profileDatabasePath(const QString &dataHome)
{
    // Same layout Database uses below: <XDG_DATA_HOME>/<org>/<app>.
    return dataHome
        + QStringLiteral("/KDE-Test/Kondor-Bookmarks-Test/kondor.sqlite");
}

// Opens a profile database outside the singleton, so the migration tests can
// prepare and inspect the databases of other profiles.
QSqlDatabase openProfileDatabase(const QString &path, const QString &connection)
{
    QSqlDatabase db = QSqlDatabase::addDatabase(QStringLiteral("QSQLITE"), connection);
    db.setDatabaseName(path);
    db.open();
    return db;
}

void closeProfileDatabase(QSqlDatabase &db)
{
    const QString connection = db.connectionName();
    db.close();
    db = QSqlDatabase();
    QSqlDatabase::removeDatabase(connection);
}

// Runs this test binary in child mode, where a fresh Database (and therefore
// its migrations) opens against the given profile directory.
bool migrateProfile(const QString &dataHome)
{
    QProcessEnvironment env = QProcessEnvironment::systemEnvironment();
    env.insert(QStringLiteral("XDG_DATA_HOME"), dataHome);
    env.insert(QStringLiteral("XDG_CONFIG_HOME"), dataHome);
    env.insert(QStringLiteral("XDG_CACHE_HOME"), dataHome);

    QProcess process;
    process.setProcessEnvironment(env);
    process.start(QCoreApplication::applicationFilePath(),
                  {QStringLiteral("--migrate"), dataHome});
    if (!process.waitForFinished(30000))
        return false;
    return process.exitStatus() == QProcess::NormalExit && process.exitCode() == 0;
}

int countRows(QSqlDatabase &db, const QString &sql)
{
    QSqlQuery query(db);
    if (!query.exec(sql) || !query.next())
        return -1;
    return query.value(0).toInt();
}
}

class TestBookmarks : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void defaultBookmarksOnFirstRun();
    void existingBookmarksAreNotReplaced();
    void deletedDefaultsStayDeleted();
    void rootFolders();
    void addAndFindBookmarks();
    void searchBookmarksFindsTitlesAndUrls();
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

void TestBookmarks::defaultBookmarksOnFirstRun()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const QVariantList toolbar = manager->folderContents(manager->toolbarFolderId());

    const QStringList titles = {
        QStringLiteral("KDE"),         QStringLiteral("Planet KDE"),
        QStringLiteral("Qt Docs"),     QStringLiteral("News"),
        QStringLiteral("Development"), QStringLiteral("Linux"),
    };
    QCOMPARE(toolbar.size(), titles.size());
    for (int i = 0; i < toolbar.size(); ++i)
        QCOMPARE(toolbar.at(i).toMap().value(QStringLiteral("title")).toString(), titles.at(i));

    // Bookmark titles are site names; the first three sit next to the folders.
    QCOMPARE(toolbar.at(0).toMap().value(QStringLiteral("url")).toString(),
             QStringLiteral("https://kde.org/"));
    QCOMPARE(toolbar.at(1).toMap().value(QStringLiteral("url")).toString(),
             QStringLiteral("https://planet.kde.org/"));
    QCOMPARE(toolbar.at(2).toMap().value(QStringLiteral("url")).toString(),
             QStringLiteral("https://doc.qt.io/"));
    QVERIFY(toolbar.at(3).toMap().value(QStringLiteral("isFolder")).toBool());
    QVERIFY(toolbar.at(4).toMap().value(QStringLiteral("isFolder")).toBool());
    QVERIFY(toolbar.at(5).toMap().value(QStringLiteral("isFolder")).toBool());

    const QVariantList newsRows =
        manager->folderContents(toolbar.at(3).toMap().value(QStringLiteral("id")).toLongLong());
    const QVariantList developmentRows =
        manager->folderContents(toolbar.at(4).toMap().value(QStringLiteral("id")).toLongLong());
    const QVariantList linuxRows =
        manager->folderContents(toolbar.at(5).toMap().value(QStringLiteral("id")).toLongLong());
    QCOMPARE(newsRows.size(), 6);
    QCOMPARE(developmentRows.size(), 6);
    QCOMPARE(linuxRows.size(), 7);

    QCOMPARE(newsRows.at(0).toMap().value(QStringLiteral("title")).toString(),
             QStringLiteral("LWN.net"));
    QCOMPARE(newsRows.at(0).toMap().value(QStringLiteral("url")).toString(),
             QStringLiteral("https://lwn.net/"));
    QCOMPARE(developmentRows.at(1).toMap().value(QStringLiteral("title")).toString(),
             QStringLiteral("KDE Human Interface Guidelines"));
    QCOMPARE(linuxRows.last().toMap().value(QStringLiteral("title")).toString(),
             QStringLiteral("KDE Discuss"));
    QCOMPARE(linuxRows.last().toMap().value(QStringLiteral("url")).toString(),
             QStringLiteral("https://discuss.kde.org/"));

    // "Other Bookmarks" stays empty.
    QCOMPARE(manager->childCount(manager->otherFolderId()), 0);
}

void TestBookmarks::existingBookmarksAreNotReplaced()
{
    QTemporaryDir dir;
    QVERIFY(dir.isValid());
    const QString path = profileDatabasePath(dir.path());
    QVERIFY(QDir().mkpath(QFileInfo(path).absolutePath()));

    // A version 2 profile that already has one user bookmark.
    {
        QSqlDatabase db = openProfileDatabase(path, QStringLiteral("prepare-v2"));
        QVERIFY(db.isOpen());
        QSqlQuery query(db);
        QVERIFY(query.exec(QStringLiteral(
            "CREATE TABLE bookmarks ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  parent_id INTEGER REFERENCES bookmarks(id) ON DELETE CASCADE,"
            "  is_folder INTEGER NOT NULL DEFAULT 0,"
            "  title TEXT NOT NULL DEFAULT '',"
            "  url TEXT,"
            "  position INTEGER NOT NULL DEFAULT 0,"
            "  created_at INTEGER NOT NULL,"
            "  special TEXT"
            ")")));
        QVERIFY(query.exec(QStringLiteral(
            "INSERT INTO bookmarks (parent_id, is_folder, title, url, position,"
            " created_at, special) VALUES "
            "(NULL, 1, 'Bookmarks Toolbar', NULL, 0, 1, 'toolbar'),"
            "(NULL, 1, 'Other Bookmarks', NULL, 0, 1, 'other'),"
            "(1, 0, 'Mine', 'https://mine.example/', 0, 1, NULL)")));
        QVERIFY(query.exec(QStringLiteral("PRAGMA user_version = 2")));
        closeProfileDatabase(db);
    }

    QVERIFY(migrateProfile(dir.path()));

    QSqlDatabase db = openProfileDatabase(path, QStringLiteral("inspect-v2"));
    QVERIFY(db.isOpen());
    QCOMPARE(countRows(db, QStringLiteral("PRAGMA user_version")), 4);
    // The two roots plus the user's bookmark: nothing was added.
    QCOMPARE(countRows(db, QStringLiteral("SELECT COUNT(*) FROM bookmarks")), 3);
    QCOMPARE(countRows(db,
                       QStringLiteral("SELECT COUNT(*) FROM bookmarks WHERE title = 'News'")),
             0);
    QCOMPARE(countRows(
                 db, QStringLiteral(
                         "SELECT COUNT(*) FROM bookmarks WHERE title = 'Mine'")),
             1);
    closeProfileDatabase(db);
}

void TestBookmarks::deletedDefaultsStayDeleted()
{
    QTemporaryDir dir;
    QVERIFY(dir.isValid());
    const QString path = profileDatabasePath(dir.path());
    QVERIFY(migrateProfile(dir.path()));

    int remaining = 0;
    {
        QSqlDatabase db = openProfileDatabase(path, QStringLiteral("delete-default"));
        QVERIFY(db.isOpen());
        QCOMPARE(countRows(db, QStringLiteral(
                                    "SELECT COUNT(*) FROM bookmarks WHERE title = 'Qt Docs'")),
                 1);
        QSqlQuery query(db);
        QVERIFY(query.exec(QStringLiteral(
            "DELETE FROM bookmarks WHERE title = 'Qt Docs' AND url = 'https://doc.qt.io/'")));
        remaining = countRows(db, QStringLiteral("SELECT COUNT(*) FROM bookmarks"));
        closeProfileDatabase(db);
    }

    // Re-opening the profile runs no seeding: the version is already current.
    QVERIFY(migrateProfile(dir.path()));

    QSqlDatabase db = openProfileDatabase(path, QStringLiteral("inspect-deleted"));
    QVERIFY(db.isOpen());
    QCOMPARE(countRows(db, QStringLiteral(
                                "SELECT COUNT(*) FROM bookmarks WHERE title = 'Qt Docs'")),
             0);
    QCOMPARE(countRows(db, QStringLiteral("SELECT COUNT(*) FROM bookmarks")), remaining);
    closeProfileDatabase(db);
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
    const int toolbarChildren = manager->childCount(toolbar);
    const qint64 second = manager->addBookmark(url, QStringLiteral("Page again"), toolbar);
    QVERIFY(second > 0);
    QVERIFY(second != first);
    QCOMPARE(manager->childCount(toolbar), toolbarChildren + 1);

    const QVariantMap info = manager->bookmark(first);
    QCOMPARE(info.value(QStringLiteral("parentId")).toLongLong(), other);
    QCOMPARE(info.value(QStringLiteral("title")).toString(), QStringLiteral("Page"));
}

void TestBookmarks::searchBookmarksFindsTitlesAndUrls()
{
    BookmarkManager *manager = BookmarkManager::instance();
    const qint64 folder = manager->addFolder(QStringLiteral("Search folder"),
                                             manager->otherFolderId());
    QVERIFY(manager->addBookmark(QUrl(QStringLiteral("https://searchable.example/")),
                                 QStringLiteral("Searchable Site"), folder) > 0);
    QVERIFY(manager->addBookmark(QUrl(QStringLiteral("https://other.example/unique-url")),
                                 QStringLiteral("Other"), folder) > 0);

    const QVariantList byTitle = manager->search(QStringLiteral("searchable"));
    QCOMPARE(byTitle.size(), 1);
    const QVariantMap entry = byTitle.at(0).toMap();
    QCOMPARE(entry.value(QStringLiteral("type")).toString(), QStringLiteral("bookmark"));
    QCOMPARE(entry.value(QStringLiteral("title")).toString(), QStringLiteral("Searchable Site"));
    QCOMPARE(entry.value(QStringLiteral("url")).toString(),
             QStringLiteral("https://searchable.example/"));

    const QVariantList byUrl = manager->search(QStringLiteral("unique-url"));
    QCOMPARE(byUrl.size(), 1);
    QCOMPARE(byUrl.at(0).toMap().value(QStringLiteral("title")).toString(),
             QStringLiteral("Other"));

    // Folders never show up, and the limit is honoured.
    QVERIFY(manager->search(QStringLiteral("Search folder")).isEmpty());
    QCOMPARE(manager->search(QStringLiteral("e"), 1).size(), 1);
    QVERIFY(manager->search(QStringLiteral("   ")).isEmpty());
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

    // Child mode used by the migration tests: open the database of the profile
    // given on the command line (through the singleton, so migrations run) and
    // exit. The caller passes the matching XDG_* variables.
    if (argc >= 3 && qstrcmp(argv[1], "--migrate") == 0) {
        qputenv("XDG_DATA_HOME", argv[2]);
        return Database::instance()->isValid() ? 0 : 1;
    }

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
