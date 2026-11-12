#include <QTemporaryDir>

#include "bookmarks/bookmarkmanager.h"
#include "bookmarkimportharness.h"
#include "bookmarksprofileharness.h"
#include "core/database.h"

class TestBookmarkImport : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void importsEveryBookmark();
    void rebuildsTheFolderTreeUnderOtherBookmarks();
    void appendsTheImportedFolder();
    void decodesEntitiesAboveTheBasicPlane();

private:
    QTemporaryDir m_dir;
    int m_importedCount = 0;
    int m_otherChildrenBeforeImport = 0;
};

void TestBookmarkImport::initTestCase()
{
    QVERIFY2(Database::instance()->isValid(), "the test database must open");
    QVERIFY(m_dir.isValid());
    const QString path = m_dir.filePath(QStringLiteral("bookmarks.html"));
    QVERIFY(writeSampleBookmarksHtml(path));
    BookmarkManager *manager = BookmarkManager::instance();
    m_otherChildrenBeforeImport = manager->childCount(manager->otherFolderId());
    m_importedCount = manager->importHtml(QUrl::fromLocalFile(path));
}

void TestBookmarkImport::importsEveryBookmark()
{
    BookmarkManager *manager = BookmarkManager::instance();
    QCOMPARE(m_importedCount, 3);
    QVERIFY(manager->isBookmarked(QUrl(QStringLiteral("https://kde.org/"))));
    QVERIFY(manager->isBookmarked(QUrl(QStringLiteral("https://planet.kde.org/"))));
    QVERIFY(manager->isBookmarked(QUrl(QStringLiteral("https://bookmarks.example/emoji"))));
}

void TestBookmarkImport::rebuildsTheFolderTreeUnderOtherBookmarks()
{
    QVERIFY(importedFolderId() > 0);
    QVERIFY(importedToolbarId() > 0);
    QVERIFY(nestedFolderId() > 0);
    const QVariantMap imported = BookmarkManager::instance()->bookmark(importedFolderId());
    QCOMPARE(imported.value(QStringLiteral("parentId")).toLongLong(),
             BookmarkManager::instance()->otherFolderId());
    const QVariantMap nested = BookmarkManager::instance()->bookmark(nestedFolderId());
    QCOMPARE(nested.value(QStringLiteral("parentId")).toLongLong(), importedToolbarId());
}

void TestBookmarkImport::appendsTheImportedFolder()
{
    const QVariantMap imported = BookmarkManager::instance()->bookmark(importedFolderId());
    QCOMPARE(imported.value(QStringLiteral("position")).toInt(), m_otherChildrenBeforeImport);
}

void TestBookmarkImport::decodesEntitiesAboveTheBasicPlane()
{
    bool foundEmoji = false;
    const QVariantList rows = BookmarkManager::instance()->folderContents(importedFolderId());
    for (const QVariant &row : rows) {
        if (fieldOf(row, "url").toString() != QLatin1String("https://bookmarks.example/emoji"))
            continue;
        QCOMPARE(fieldOf(row, "title").toString(), QStringLiteral("Emoji \U0001F600 \U0001F600"));
        foundEmoji = true;
    }
    QVERIFY(foundEmoji);
}

int runTestBookmarkImport(int argc, char *argv[])
{
    TestBookmarkImport test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_bookmarkimport.moc"
