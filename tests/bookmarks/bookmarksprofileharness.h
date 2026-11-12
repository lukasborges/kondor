#pragma once

#include <QDir>
#include <QFileInfo>
#include <QProcess>
#include <QSqlDatabase>
#include <QSqlQuery>
#include <QTest>
#include <QVariantMap>

inline QString profileDatabasePath(const QString &dataHome)
{
    return dataHome + QStringLiteral("/KDE-Test/Kondor-Bookmarks-Test/kondor.sqlite");
}

inline QSqlDatabase openProfileDatabase(const QString &path, const QString &connection)
{
    QSqlDatabase db = QSqlDatabase::addDatabase(QStringLiteral("QSQLITE"), connection);
    db.setDatabaseName(path);
    db.open();
    return db;
}

inline void closeProfileDatabase(QSqlDatabase &db)
{
    const QString connection = db.connectionName();
    db.close();
    db = QSqlDatabase();
    QSqlDatabase::removeDatabase(connection);
}

inline QProcessEnvironment environmentFor(const QString &dataHome)
{
    QProcessEnvironment env = QProcessEnvironment::systemEnvironment();
    env.insert(QStringLiteral("XDG_DATA_HOME"), dataHome);
    env.insert(QStringLiteral("XDG_CONFIG_HOME"), dataHome);
    env.insert(QStringLiteral("XDG_CACHE_HOME"), dataHome);
    return env;
}

inline bool migrateProfile(const QString &dataHome)
{
    QProcess process;
    process.setProcessEnvironment(environmentFor(dataHome));
    process.start(QCoreApplication::applicationFilePath(), {QStringLiteral("--migrate"), dataHome});
    if (!process.waitForFinished(30000))
        return false;
    return process.exitStatus() == QProcess::NormalExit && process.exitCode() == 0;
}

inline int countRows(QSqlDatabase &db, const QString &sql)
{
    QSqlQuery query(db);
    if (!query.exec(sql) || !query.next())
        return -1;
    return query.value(0).toInt();
}

inline int countTitled(QSqlDatabase &db, const QString &title)
{
    return countRows(db, QStringLiteral("SELECT COUNT(*) FROM bookmarks WHERE title = '%1'").arg(title));
}

inline QString createVersion2BookmarksTable()
{
    return QStringLiteral(
        "CREATE TABLE bookmarks ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  parent_id INTEGER REFERENCES bookmarks(id) ON DELETE CASCADE,"
        "  is_folder INTEGER NOT NULL DEFAULT 0,"
        "  title TEXT NOT NULL DEFAULT '',"
        "  url TEXT,"
        "  position INTEGER NOT NULL DEFAULT 0,"
        "  created_at INTEGER NOT NULL,"
        "  special TEXT"
        ")");
}

inline QString insertRootsAndOneUserBookmark()
{
    return QStringLiteral(
        "INSERT INTO bookmarks (parent_id, is_folder, title, url, position,"
        " created_at, special) VALUES "
        "(NULL, 1, 'Bookmarks Toolbar', NULL, 0, 1, 'toolbar'),"
        "(NULL, 1, 'Other Bookmarks', NULL, 0, 1, 'other'),"
        "(1, 0, 'Mine', 'https://mine.example/', 0, 1, NULL)");
}

inline bool seedVersion2Profile(const QString &path)
{
    QSqlDatabase db = openProfileDatabase(path, QStringLiteral("prepare-v2"));
    QSqlQuery query(db);
    const bool seeded = db.isOpen() && query.exec(createVersion2BookmarksTable())
        && query.exec(insertRootsAndOneUserBookmark())
        && query.exec(QStringLiteral("PRAGMA user_version = 2"));
    query.finish();
    closeProfileDatabase(db);
    return seeded;
}

inline int deleteQtDocsDefaultAndCountRemaining(const QString &path)
{
    QSqlDatabase db = openProfileDatabase(path, QStringLiteral("delete-default"));
    QSqlQuery query(db);
    const bool deleted = db.isOpen() && countTitled(db, QStringLiteral("Qt Docs")) == 1
        && query.exec(QStringLiteral(
            "DELETE FROM bookmarks WHERE title = 'Qt Docs' AND url = 'https://doc.qt.io/'"));
    const int remaining = deleted ? countRows(db, QStringLiteral("SELECT COUNT(*) FROM bookmarks")) : -1;
    query.finish();
    closeProfileDatabase(db);
    return remaining;
}

inline QVariant fieldOf(const QVariant &row, const char *key)
{
    return row.toMap().value(QLatin1String(key));
}

int runTestDefaultBookmarks(int argc, char *argv[]);
int runTestBookmarkTree(int argc, char *argv[]);
int runTestBookmarkImport(int argc, char *argv[]);
