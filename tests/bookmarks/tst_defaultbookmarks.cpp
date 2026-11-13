#include <QTemporaryDir>

#include "bookmarks/bookmarkmanager.h"
#include "bookmarksprofileharness.h"
#include "core/database/database.h"

class TestDefaultBookmarks : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void toolbarHoldsSiteBookmarksThenFolders();
    void defaultFoldersHaveTheirSizes();
    void defaultFoldersHoldTheirBookmarks();
    void otherBookmarksStaysEmpty();
    void existingBookmarksAreNotReplaced();
    void deletedDefaultsStayDeleted();

private:
    QVariantList toolbarRows() const;
    QVariantList folderRows(const QVariant &folderRow) const;
};

QVariantList TestDefaultBookmarks::toolbarRows() const
{
    BookmarkManager *manager = BookmarkManager::instance();
    return manager->folderContents(manager->toolbarFolderId());
}

QVariantList TestDefaultBookmarks::folderRows(const QVariant &folderRow) const
{
    return BookmarkManager::instance()->folderContents(fieldOf(folderRow, "id").toLongLong());
}

void TestDefaultBookmarks::initTestCase()
{
    QVERIFY2(Database::instance()->isValid(), "the test database must open");
}

void TestDefaultBookmarks::toolbarHoldsSiteBookmarksThenFolders()
{
    const QVariantList toolbar = toolbarRows();
    const QStringList titles = {
        QStringLiteral("KDE"),         QStringLiteral("Planet KDE"),
        QStringLiteral("Qt Docs"),     QStringLiteral("News"),
        QStringLiteral("Development"), QStringLiteral("Linux"),
    };
    QCOMPARE(toolbar.size(), titles.size());
    for (int i = 0; i < toolbar.size(); ++i)
        QCOMPARE(fieldOf(toolbar.at(i), "title").toString(), titles.at(i));
    QCOMPARE(fieldOf(toolbar.at(0), "url").toString(), QStringLiteral("https://kde.org/"));
    QCOMPARE(fieldOf(toolbar.at(1), "url").toString(), QStringLiteral("https://planet.kde.org/"));
    QCOMPARE(fieldOf(toolbar.at(2), "url").toString(), QStringLiteral("https://doc.qt.io/"));
    QVERIFY(fieldOf(toolbar.at(3), "isFolder").toBool());
    QVERIFY(fieldOf(toolbar.at(4), "isFolder").toBool());
    QVERIFY(fieldOf(toolbar.at(5), "isFolder").toBool());
}

void TestDefaultBookmarks::defaultFoldersHaveTheirSizes()
{
    const QVariantList toolbar = toolbarRows();
    QCOMPARE(folderRows(toolbar.at(3)).size(), 6);
    QCOMPARE(folderRows(toolbar.at(4)).size(), 6);
    QCOMPARE(folderRows(toolbar.at(5)).size(), 7);
}

void TestDefaultBookmarks::defaultFoldersHoldTheirBookmarks()
{
    const QVariantList toolbar = toolbarRows();
    const QVariantList newsRows = folderRows(toolbar.at(3));
    const QVariantList developmentRows = folderRows(toolbar.at(4));
    const QVariantList linuxRows = folderRows(toolbar.at(5));
    QCOMPARE(fieldOf(newsRows.at(0), "title").toString(), QStringLiteral("LWN.net"));
    QCOMPARE(fieldOf(newsRows.at(0), "url").toString(), QStringLiteral("https://lwn.net/"));
    QCOMPARE(fieldOf(developmentRows.at(1), "title").toString(),
             QStringLiteral("KDE Human Interface Guidelines"));
    QCOMPARE(fieldOf(linuxRows.last(), "title").toString(), QStringLiteral("KDE Discuss"));
    QCOMPARE(fieldOf(linuxRows.last(), "url").toString(), QStringLiteral("https://discuss.kde.org/"));
}

void TestDefaultBookmarks::otherBookmarksStaysEmpty()
{
    BookmarkManager *manager = BookmarkManager::instance();
    QCOMPARE(manager->childCount(manager->otherFolderId()), 0);
}

void TestDefaultBookmarks::existingBookmarksAreNotReplaced()
{
    QTemporaryDir dir;
    QVERIFY(dir.isValid());
    const QString path = profileDatabasePath(dir.path());
    QVERIFY(QDir().mkpath(QFileInfo(path).absolutePath()));
    QVERIFY(seedVersion2Profile(path));
    QVERIFY(migrateProfile(dir.path()));
    QSqlDatabase db = openProfileDatabase(path, QStringLiteral("inspect-v2"));
    QVERIFY(db.isOpen());
    QCOMPARE(countRows(db, QStringLiteral("PRAGMA user_version")), 5);
    QCOMPARE(countRows(db, QStringLiteral("SELECT COUNT(*) FROM bookmarks")), 3);
    QCOMPARE(countTitled(db, QStringLiteral("News")), 0);
    QCOMPARE(countTitled(db, QStringLiteral("Mine")), 1);
    closeProfileDatabase(db);
}

void TestDefaultBookmarks::deletedDefaultsStayDeleted()
{
    QTemporaryDir dir;
    QVERIFY(dir.isValid());
    const QString path = profileDatabasePath(dir.path());
    QVERIFY(migrateProfile(dir.path()));
    const int remaining = deleteQtDocsDefaultAndCountRemaining(path);
    QVERIFY(remaining >= 0);
    QVERIFY(migrateProfile(dir.path()));
    QSqlDatabase db = openProfileDatabase(path, QStringLiteral("inspect-deleted"));
    QVERIFY(db.isOpen());
    QCOMPARE(countTitled(db, QStringLiteral("Qt Docs")), 0);
    QCOMPARE(countRows(db, QStringLiteral("SELECT COUNT(*) FROM bookmarks")), remaining);
    closeProfileDatabase(db);
}

int runTestDefaultBookmarks(int argc, char *argv[])
{
    TestDefaultBookmarks test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_defaultbookmarks.moc"
