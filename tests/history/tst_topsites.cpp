#include <QCoreApplication>
#include <QStandardPaths>
#include <QTemporaryDir>

#include "common/isolatedhome.h"
#include "topsitesharness.h"

class TestTopSites : public QObject
{
    Q_OBJECT

private slots:
    void init();
    void groupsByHostAndSortsByVisits();
    void stripsWwwAndIgnoresOtherSchemes();
    void skipsHiddenHosts();
    void ignoresVisitsOlderThanNinetyDays();
};

void TestTopSites::init()
{
    resetHistory();
}

void TestTopSites::groupsByHostAndSortsByVisits()
{
    addGroupedVisits();
    const QVariantList sites = HistoryManager::instance()->topSites(8);
    QCOMPARE(sites.size(), 3);
    QCOMPARE(fieldOf(sites.at(0), "host"), QStringLiteral("kde.org"));
    QCOMPARE(fieldOf(sites.at(0), "url"), QStringLiteral("https://kde.org/a"));
    QCOMPARE(fieldOf(sites.at(0), "title"), QStringLiteral("A latest"));
    QCOMPARE(fieldOf(sites.at(1), "host"), QStringLiteral("wikipedia.org"));
    QCOMPARE(fieldOf(sites.at(2), "host"), QStringLiteral("fedoraproject.org"));
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
    QCOMPARE(fieldOf(sites.at(0), "host"), QStringLiteral("example.org"));
}

void TestTopSites::skipsHiddenHosts()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    addVisit(QStringLiteral("https://kde.org/"), QStringLiteral("KDE"), now - 1000);
    addVisit(QStringLiteral("https://wikipedia.org/"), QStringLiteral("Wiki"), now - 2000);
    Settings::instance()->setHiddenTopSites({QStringLiteral("kde.org")});
    const QVariantList sites = HistoryManager::instance()->topSites(8);
    QCOMPARE(sites.size(), 1);
    QCOMPARE(fieldOf(sites.at(0), "host"), QStringLiteral("wikipedia.org"));
}

void TestTopSites::ignoresVisitsOlderThanNinetyDays()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    const qint64 ninetyOneDays = 91LL * 24 * 60 * 60 * 1000;
    addVisit(QStringLiteral("https://old.example/"), QStringLiteral("Old"), now - ninetyOneDays);
    addVisit(QStringLiteral("https://new.example/"), QStringLiteral("New"), now - 1000);
    const QVariantList sites = HistoryManager::instance()->topSites(8);
    QCOMPARE(sites.size(), 1);
    QCOMPARE(fieldOf(sites.at(0), "host"), QStringLiteral("new.example"));
}

int main(int argc, char *argv[])
{
    QStandardPaths::setTestModeEnabled(true);
    QCoreApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("KDE"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor"));
    QTemporaryDir home;
    if (!useIsolatedHome(home))
        return 1;
    TestTopSites test;
    const int topSitesFailures = QTest::qExec(&test, argc, argv);
    return topSitesFailures + runTestHistorySuggestions(argc, argv);
}

#include "tst_topsites.moc"
