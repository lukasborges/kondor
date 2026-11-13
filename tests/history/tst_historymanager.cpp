#include <QCoreApplication>
#include <QDateTime>
#include <QSqlQuery>
#include <QStandardPaths>
#include <QTest>

#include "core/database/database.h"
#include "history/historymanager.h"

class TestHistoryManager : public QObject
{
    Q_OBJECT

private slots:
    void init();
    void addVisitIgnoresUnsupportedSchemes();
    void revisitWithinWindowUpdatesTitleOnly();
    void updateTitleLeavesOlderVisitsUntouched();
    void clearSinceKeepsOlderVisits();
    void removeEntryDeletesOnlyThatRow();

private:
    static void insertVisit(const QString &url, const QString &title, qint64 visitedAt);
    static QStringList titles();
    static qint64 idOfTitle(const QString &title);
};

void TestHistoryManager::init()
{
    QVERIFY(Database::instance()->isValid());
    QSqlQuery clear(Database::instance()->handle());
    QVERIFY(clear.exec(QStringLiteral("DELETE FROM history")));
}

void TestHistoryManager::insertVisit(const QString &url, const QString &title, qint64 visitedAt)
{
    QSqlQuery insert(Database::instance()->handle());
    insert.prepare(QStringLiteral(
        "INSERT INTO history (url, title, visited_at) VALUES (?, ?, ?)"));
    insert.addBindValue(url);
    insert.addBindValue(title);
    insert.addBindValue(visitedAt);
    QVERIFY(insert.exec());
}

QStringList TestHistoryManager::titles()
{
    QStringList result;
    QSqlQuery query(Database::instance()->handle());
    query.exec(QStringLiteral("SELECT title FROM history ORDER BY visited_at, id"));
    while (query.next())
        result.append(query.value(0).toString());
    return result;
}

qint64 TestHistoryManager::idOfTitle(const QString &title)
{
    QSqlQuery query(Database::instance()->handle());
    query.prepare(QStringLiteral("SELECT id FROM history WHERE title = ?"));
    query.addBindValue(title);
    query.exec();
    return query.next() ? query.value(0).toLongLong() : -1;
}

void TestHistoryManager::addVisitIgnoresUnsupportedSchemes()
{
    HistoryManager *manager = HistoryManager::instance();
    manager->addVisit(QUrl(QStringLiteral("about:blank")), QStringLiteral("Blank"));
    manager->addVisit(QUrl(QStringLiteral("ftp://example.org/")), QStringLiteral("Ftp"));
    manager->addVisit(QUrl(), QStringLiteral("Empty"));
    QVERIFY(titles().isEmpty());
    manager->addVisit(QUrl(QStringLiteral("https://example.org/")), QStringLiteral("Web"));
    QCOMPARE(titles(), QStringList{QStringLiteral("Web")});
}

void TestHistoryManager::revisitWithinWindowUpdatesTitleOnly()
{
    HistoryManager *manager = HistoryManager::instance();
    const QUrl url(QStringLiteral("https://example.org/"));
    manager->addVisit(url, QStringLiteral("First"));
    manager->addVisit(url, QStringLiteral("Second"));
    QCOMPARE(titles(), QStringList{QStringLiteral("Second")});
}

void TestHistoryManager::updateTitleLeavesOlderVisitsUntouched()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    insertVisit(QStringLiteral("https://example.org/"), QStringLiteral("Old"), now - 60000);
    insertVisit(QStringLiteral("https://example.org/"), QStringLiteral("Recent"), now - 1000);
    HistoryManager::instance()->updateTitle(QUrl(QStringLiteral("https://example.org/")),
                                            QStringLiteral("Renamed"));
    QCOMPARE(titles(), (QStringList{QStringLiteral("Old"), QStringLiteral("Renamed")}));
}

void TestHistoryManager::clearSinceKeepsOlderVisits()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    insertVisit(QStringLiteral("https://a.example/"), QStringLiteral("Older"), now - 5000);
    insertVisit(QStringLiteral("https://b.example/"), QStringLiteral("Newer"), now - 1000);
    HistoryManager::instance()->clearSince(now - 2000);
    QCOMPARE(titles(), QStringList{QStringLiteral("Older")});
}

void TestHistoryManager::removeEntryDeletesOnlyThatRow()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    insertVisit(QStringLiteral("https://a.example/"), QStringLiteral("Keep"), now - 5000);
    insertVisit(QStringLiteral("https://b.example/"), QStringLiteral("Drop"), now - 1000);
    HistoryManager::instance()->removeEntry(idOfTitle(QStringLiteral("Drop")));
    QCOMPARE(titles(), QStringList{QStringLiteral("Keep")});
}

int main(int argc, char *argv[])
{
    QStandardPaths::setTestModeEnabled(true);
    QCoreApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("KDE"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor"));

    TestHistoryManager test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_historymanager.moc"
