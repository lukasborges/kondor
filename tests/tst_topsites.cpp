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
