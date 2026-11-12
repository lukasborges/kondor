#include "topsitesharness.h"

class TestHistorySuggestions : public QObject
{
    Q_OBJECT

private slots:
    void init();
    void suggestMatchesUrlAndTitle();
    void suggestSortsByVisitsAndLimit();
    void suggestEscapesWildcards();
    void hostCompletionPrefersMostVisitedHost();
    void recentTodayExcludesYesterday();
};

void TestHistorySuggestions::init()
{
    resetHistory();
}

void TestHistorySuggestions::suggestMatchesUrlAndTitle()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    addVisit(QStringLiteral("https://kde.org/"), QStringLiteral("KDE Community"), now - 1000);
    addVisit(QStringLiteral("https://plasma.kde.org/"), QStringLiteral("Plasma"), now - 2000);
    const QVariantList byUrl = HistoryManager::instance()->suggest(QStringLiteral("plasma"));
    QCOMPARE(byUrl.size(), 1);
    QCOMPARE(fieldOf(byUrl.at(0), "type"), QStringLiteral("history"));
    QCOMPARE(fieldOf(byUrl.at(0), "url"), QStringLiteral("https://plasma.kde.org/"));
    QCOMPARE(fieldOf(byUrl.at(0), "title"), QStringLiteral("Plasma"));
    const QVariantList byTitle = HistoryManager::instance()->suggest(QStringLiteral("community"));
    QCOMPARE(byTitle.size(), 1);
    QCOMPARE(fieldOf(byTitle.at(0), "url"), QStringLiteral("https://kde.org/"));
    QVERIFY(HistoryManager::instance()->suggest(QStringLiteral("   ")).isEmpty());
}

void TestHistorySuggestions::suggestSortsByVisitsAndLimit()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    addVisit(QStringLiteral("https://a.example/"), QStringLiteral("Example A"), now - 3000);
    addVisit(QStringLiteral("https://b.example/"), QStringLiteral("Example B"), now - 2000);
    addVisit(QStringLiteral("https://b.example/"), QStringLiteral("Example B"), now - 1000);
    const QVariantList all = HistoryManager::instance()->suggest(QStringLiteral("example"));
    QCOMPARE(all.size(), 2);
    QCOMPARE(fieldOf(all.at(0), "url"), QStringLiteral("https://b.example/"));
    QCOMPARE(HistoryManager::instance()->suggest(QStringLiteral("example"), 1).size(), 1);
}

void TestHistorySuggestions::suggestEscapesWildcards()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    addVisit(QStringLiteral("https://example.org/100%25"), QStringLiteral("Percent"), now - 1000);
    addVisit(QStringLiteral("https://example.org/other"), QStringLiteral("Other"), now - 2000);
    QCOMPARE(HistoryManager::instance()->suggest(QStringLiteral("%")).size(), 1);
    QCOMPARE(HistoryManager::instance()->suggest(QStringLiteral("000_")).size(), 0);
}

void TestHistorySuggestions::hostCompletionPrefersMostVisitedHost()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    addVisit(QStringLiteral("https://www.kde.org/"), QStringLiteral("KDE"), now - 2000);
    addVisit(QStringLiteral("https://kde.org/announcements/"), QStringLiteral("KDE news"), now - 1000);
    addVisit(QStringLiteral("https://example.org/kde-guide"), QStringLiteral("Guide"), now - 3000);
    QCOMPARE(HistoryManager::instance()->hostCompletion(QStringLiteral("kd")), QStringLiteral("kde.org"));
    QCOMPARE(HistoryManager::instance()->hostCompletion(QStringLiteral("kde.o")), QStringLiteral("kde.org"));
    QCOMPARE(HistoryManager::instance()->hostCompletion(QStringLiteral("kde.org")), QString());
    QCOMPARE(HistoryManager::instance()->hostCompletion(QStringLiteral("kde p")), QString());
    QCOMPARE(HistoryManager::instance()->hostCompletion(QStringLiteral("zzz")), QString());
}

void TestHistorySuggestions::recentTodayExcludesYesterday()
{
    const qint64 midnight = QDateTime(QDate::currentDate(), QTime(0, 0)).toMSecsSinceEpoch();
    addVisit(QStringLiteral("https://old.example/"), QStringLiteral("Old"), midnight - 1000);
    addVisit(QStringLiteral("https://a.example/"), QStringLiteral("A"), midnight + 1000);
    addVisit(QStringLiteral("https://b.example/"), QStringLiteral("B"), midnight + 2000);
    addVisit(QStringLiteral("https://a.example/"), QStringLiteral("A"), midnight + 3000);
    const QVariantList today = HistoryManager::instance()->recentToday(8);
    QCOMPARE(today.size(), 2);
    QCOMPARE(fieldOf(today.at(0), "url"), QStringLiteral("https://a.example/"));
    QCOMPARE(fieldOf(today.at(1), "url"), QStringLiteral("https://b.example/"));
    QCOMPARE(HistoryManager::instance()->recentToday(1).size(), 1);
}

int runTestHistorySuggestions(int argc, char *argv[])
{
    TestHistorySuggestions test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_historysuggestions.moc"
