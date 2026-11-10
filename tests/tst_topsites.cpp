#include <QCoreApplication>
#include <QDateTime>
#include <QSqlQuery>
#include <QStandardPaths>
#include <QTest>
#include <QVariantList>
#include <QVariantMap>

#include "database.h"
#include "historymanager.h"
#include "settings.h"

class TestTopSites : public QObject
{
    Q_OBJECT

private slots:
    void init();
    void groupsByHostAndSortsByVisits();
    void stripsWwwAndIgnoresOtherSchemes();
    void skipsHiddenHosts();
    void ignoresVisitsOlderThanNinetyDays();
    void suggestMatchesUrlAndTitle();
    void suggestSortsByVisitsAndLimit();
    void suggestEscapesWildcards();
    void hostCompletionPrefersMostVisitedHost();

private:
    void addVisit(const QString &url, const QString &title, qint64 visitedAt);
};

void TestTopSites::init()
{
    QVERIFY(Database::instance()->isValid());
    QSqlQuery clear(Database::instance()->handle());
    QVERIFY(clear.exec(QStringLiteral("DELETE FROM history")));
    Settings::instance()->setHiddenTopSites({});
}

void TestTopSites::addVisit(const QString &url, const QString &title, qint64 visitedAt)
{
    QSqlQuery insert(Database::instance()->handle());
    insert.prepare(QStringLiteral(
        "INSERT INTO history (url, title, visited_at) VALUES (?, ?, ?)"));
    insert.addBindValue(url);
    insert.addBindValue(title);
    insert.addBindValue(visitedAt);
    QVERIFY(insert.exec());
}

void TestTopSites::groupsByHostAndSortsByVisits()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    addVisit(QStringLiteral("https://kde.org/a"), QStringLiteral("A"), now - 4000);
    addVisit(QStringLiteral("https://kde.org/b"), QStringLiteral("B"), now - 3000);
    addVisit(QStringLiteral("https://kde.org/a"), QStringLiteral("A latest"), now - 2000);
    addVisit(QStringLiteral("https://wikipedia.org/"), QStringLiteral("Wiki"), now - 5000);
    addVisit(QStringLiteral("https://fedoraproject.org/"), QStringLiteral("Fedora"), now - 6000);

    const QVariantList sites = HistoryManager::instance()->topSites(8);
    QCOMPARE(sites.size(), 3);

    const QVariantMap kde = sites.at(0).toMap();
    QCOMPARE(kde.value(QStringLiteral("host")).toString(), QStringLiteral("kde.org"));
    QCOMPARE(kde.value(QStringLiteral("url")).toString(), QStringLiteral("https://kde.org/a"));
    QCOMPARE(kde.value(QStringLiteral("title")).toString(), QStringLiteral("A latest"));

    QCOMPARE(sites.at(1).toMap().value(QStringLiteral("host")).toString(),
             QStringLiteral("wikipedia.org"));
    QCOMPARE(sites.at(2).toMap().value(QStringLiteral("host")).toString(),
             QStringLiteral("fedoraproject.org"));

    QCOMPARE(HistoryManager::instance()->topSites(2).size(), 2);
}

void TestTopSites::stripsWwwAndIgnoresOtherSchemes()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    addVisit(QStringLiteral("https://www.example.org/page"), QStringLiteral("Example"), now - 1000);
    addVisit(QStringLiteral("file:///tmp/page.html"), QStringLiteral("Local"), now - 2000);
    addVisit(QStringLiteral("about:blank"), QStringLiteral("Blank"), now - 3000);

    const QVariantList sites = HistoryManager::instance()->topSites(8);
    QCOMPARE(sites.size(), 1);
    QCOMPARE(sites.at(0).toMap().value(QStringLiteral("host")).toString(),
             QStringLiteral("example.org"));
}

void TestTopSites::suggestMatchesUrlAndTitle()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    addVisit(QStringLiteral("https://kde.org/"), QStringLiteral("KDE Community"), now - 1000);
    addVisit(QStringLiteral("https://plasma.kde.org/"), QStringLiteral("Plasma"), now - 2000);

    const QVariantList byUrl = HistoryManager::instance()->suggest(QStringLiteral("plasma"));
    QCOMPARE(byUrl.size(), 1);
    const QVariantMap entry = byUrl.at(0).toMap();
    QCOMPARE(entry.value(QStringLiteral("type")).toString(), QStringLiteral("history"));
    QCOMPARE(entry.value(QStringLiteral("url")).toString(),
             QStringLiteral("https://plasma.kde.org/"));
    QCOMPARE(entry.value(QStringLiteral("title")).toString(), QStringLiteral("Plasma"));

    // Title matches count too.
    const QVariantList byTitle = HistoryManager::instance()->suggest(QStringLiteral("community"));
    QCOMPARE(byTitle.size(), 1);
    QCOMPARE(byTitle.at(0).toMap().value(QStringLiteral("url")).toString(),
             QStringLiteral("https://kde.org/"));

    QVERIFY(HistoryManager::instance()->suggest(QStringLiteral("   ")).isEmpty());
}

void TestTopSites::suggestSortsByVisitsAndLimit()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    addVisit(QStringLiteral("https://a.example/"), QStringLiteral("Example A"), now - 3000);
    addVisit(QStringLiteral("https://b.example/"), QStringLiteral("Example B"), now - 2000);
    addVisit(QStringLiteral("https://b.example/"), QStringLiteral("Example B"), now - 1000);

    const QVariantList all = HistoryManager::instance()->suggest(QStringLiteral("example"));
    QCOMPARE(all.size(), 2);
    QCOMPARE(all.at(0).toMap().value(QStringLiteral("url")).toString(),
             QStringLiteral("https://b.example/"));
    QCOMPARE(HistoryManager::instance()->suggest(QStringLiteral("example"), 1).size(), 1);
}

void TestTopSites::suggestEscapesWildcards()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    addVisit(QStringLiteral("https://example.org/100%25"), QStringLiteral("Percent"), now - 1000);
    addVisit(QStringLiteral("https://example.org/other"), QStringLiteral("Other"), now - 2000);

    // A bare % must not behave as a LIKE wildcard matching every URL.
    QCOMPARE(HistoryManager::instance()->suggest(QStringLiteral("%")).size(), 1);
    // An underscore is a literal too, not "any single character".
    QCOMPARE(HistoryManager::instance()->suggest(QStringLiteral("000_")).size(), 0);
}

void TestTopSites::hostCompletionPrefersMostVisitedHost()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    addVisit(QStringLiteral("https://www.kde.org/"), QStringLiteral("KDE"), now - 2000);
    addVisit(QStringLiteral("https://kde.org/announcements/"), QStringLiteral("KDE news"),
             now - 1000);
    addVisit(QStringLiteral("https://example.org/kde-guide"), QStringLiteral("Guide"),
             now - 3000);

    QCOMPARE(HistoryManager::instance()->hostCompletion(QStringLiteral("kd")),
             QStringLiteral("kde.org"));
    QCOMPARE(HistoryManager::instance()->hostCompletion(QStringLiteral("kde.o")),
             QStringLiteral("kde.org"));
    QCOMPARE(HistoryManager::instance()->hostCompletion(QStringLiteral("kde.org")),
             QString());
    QCOMPARE(HistoryManager::instance()->hostCompletion(QStringLiteral("kde p")),
             QString());
    QCOMPARE(HistoryManager::instance()->hostCompletion(QStringLiteral("zzz")),
             QString());
}

void TestTopSites::skipsHiddenHosts()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    addVisit(QStringLiteral("https://kde.org/"), QStringLiteral("KDE"), now - 1000);
    addVisit(QStringLiteral("https://wikipedia.org/"), QStringLiteral("Wiki"), now - 2000);

    Settings::instance()->setHiddenTopSites({QStringLiteral("kde.org")});
    const QVariantList sites = HistoryManager::instance()->topSites(8);
    QCOMPARE(sites.size(), 1);
    QCOMPARE(sites.at(0).toMap().value(QStringLiteral("host")).toString(),
             QStringLiteral("wikipedia.org"));
}

void TestTopSites::ignoresVisitsOlderThanNinetyDays()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    const qint64 ninetyOneDays = 91LL * 24 * 60 * 60 * 1000;
    addVisit(QStringLiteral("https://old.example/"), QStringLiteral("Old"), now - ninetyOneDays);
    addVisit(QStringLiteral("https://new.example/"), QStringLiteral("New"), now - 1000);

    const QVariantList sites = HistoryManager::instance()->topSites(8);
    QCOMPARE(sites.size(), 1);
    QCOMPARE(sites.at(0).toMap().value(QStringLiteral("host")).toString(),
             QStringLiteral("new.example"));
}

int main(int argc, char *argv[])
{
    // Keep the database and settings out of the real user directories.
    QStandardPaths::setTestModeEnabled(true);
    QCoreApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("KDE"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor"));

    TestTopSites test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_topsites.moc"
