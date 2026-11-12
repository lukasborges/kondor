#include <QCoreApplication>
#include <QDir>
#include <QSqlDatabase>
#include <QSqlQuery>
#include <QStandardPaths>
#include <QTest>

#include "core/database.h"
#include "core/sql.h"

class TestDatabase : public QObject
{
    Q_OBJECT

private slots:
    void upgradesVersionOneFileKeepingHistory();

private:
    void writeVersionOneFile();
    int scalar(const QString &statement);
};

void TestDatabase::writeVersionOneFile()
{
    const QString dir = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation);
    QDir().mkpath(dir);
    QSqlDatabase old = QSqlDatabase::addDatabase(QStringLiteral("QSQLITE"), QStringLiteral("old"));
    old.setDatabaseName(dir + QStringLiteral("/kondor.sqlite"));
    QVERIFY(old.open());
    QSqlQuery query(old);
    QVERIFY(query.exec(QStringLiteral("CREATE TABLE history (id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " url TEXT NOT NULL, title TEXT NOT NULL DEFAULT '', visited_at INTEGER NOT NULL)")));
    QVERIFY(query.exec(QStringLiteral("INSERT INTO history (url, title, visited_at)"
        " VALUES ('https://kde.org/', 'KDE', 1)")));
    QVERIFY(query.exec(QStringLiteral("PRAGMA user_version = 1")));
    old.close();
}

int TestDatabase::scalar(const QString &statement)
{
    auto query = Sql::run(statement);
    return query && query->next() ? query->value(0).toInt() : -1;
}

void TestDatabase::upgradesVersionOneFileKeepingHistory()
{
    QStandardPaths::setTestModeEnabled(true);
    QDir(QStandardPaths::writableLocation(QStandardPaths::AppDataLocation)).removeRecursively();
    writeVersionOneFile();
    QSqlDatabase::removeDatabase(QStringLiteral("old"));
    QVERIFY(Database::instance()->isValid());
    QCOMPARE(scalar(QStringLiteral("SELECT COUNT(*) FROM history")), 1);
    QCOMPARE(scalar(QStringLiteral("PRAGMA user_version")), 5);
    QCOMPARE(scalar(QStringLiteral("SELECT COUNT(*) FROM favicons")), 0);
    QCOMPARE(scalar(QStringLiteral("SELECT COUNT(*) FROM extension_storage")), 0);
    QCOMPARE(scalar(QStringLiteral("SELECT COUNT(*) FROM bookmarks WHERE special IN ('toolbar','other')")), 2);
}

QTEST_MAIN(TestDatabase)
#include "tst_database.moc"
