#include "database.h"

#include <QDir>
#include <QDateTime>
#include <QSqlError>
#include <QSqlQuery>
#include <QStandardPaths>
#include <QVariant>
#include <utility>

namespace {
// Schema version. Each migration bumps `PRAGMA user_version` by 1.
constexpr int kSchemaVersion = 2;
}

Database *Database::instance()
{
    static Database *db = new Database;
    return db;
}

Database::Database()
{
    const QString dir =
        QStandardPaths::writableLocation(QStandardPaths::AppDataLocation);
    QDir().mkpath(dir);
    const QString path = dir + QStringLiteral("/kondor.sqlite");

    m_db = QSqlDatabase::addDatabase(QStringLiteral("QSQLITE"), QStringLiteral("kondor"));
    m_db.setDatabaseName(path);
    if (!m_db.open()) {
        // Opens lazily and survives a missing file: without a database the
        // browser keeps working, just without history.
        qWarning("Database: failed to open %s: %s", qPrintable(path),
                 qPrintable(m_db.lastError().text()));
        return;
    }

    // A corrupted file can still "open": probe it to make sure it is a real
    // SQLite database before trusting it.
    QSqlQuery probe(m_db);
    if (!probe.exec(QStringLiteral("PRAGMA user_version"))) {
        qWarning("Database: %s is not a usable SQLite database: %s", qPrintable(path),
                 qPrintable(m_db.lastError().text()));
        m_db.close();
        return;
    }

    m_valid = true;
    migrate();
}

bool Database::isValid() const
{
    return m_valid && m_db.isOpen();
}

QSqlDatabase Database::handle() const
{
    return m_db;
}

int Database::schemaVersion() const
{
    QSqlQuery query(m_db);
    if (query.exec(QStringLiteral("PRAGMA user_version")) && query.next())
        return query.value(0).toInt();
    return 0;
}

void Database::migrate()
{
    const int current = schemaVersion();
    if (current >= kSchemaVersion)
        return;

    if (!m_db.transaction()) {
        qWarning("Database: failed to begin migration transaction: %s",
                 qPrintable(m_db.lastError().text()));
        return;
    }

    QSqlQuery query(m_db);
    bool ok = true;
    if (current < 1) {
        ok = ok && query.exec(QStringLiteral(
            "CREATE TABLE IF NOT EXISTS history ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  url TEXT NOT NULL,"
            "  title TEXT NOT NULL DEFAULT '',"
            "  visited_at INTEGER NOT NULL"
            ")"));
        ok = ok && query.exec(QStringLiteral(
            "CREATE INDEX IF NOT EXISTS history_visited_at ON history(visited_at DESC)"));
        ok = ok && query.exec(QStringLiteral(
            "CREATE INDEX IF NOT EXISTS history_url ON history(url)"));
    }
    if (current < 2) {
        // Bookmarks: a tree of folders (is_folder = 1) and bookmarks
        // (is_folder = 0). Root folders are identified by `special`
        // ('toolbar' / 'other') and can never be removed.
        ok = ok && query.exec(QStringLiteral(
            "CREATE TABLE IF NOT EXISTS bookmarks ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  parent_id INTEGER REFERENCES bookmarks(id) ON DELETE CASCADE,"
            "  is_folder INTEGER NOT NULL DEFAULT 0,"
            "  title TEXT NOT NULL DEFAULT '',"
            "  url TEXT,"
            "  position INTEGER NOT NULL DEFAULT 0,"
            "  created_at INTEGER NOT NULL,"
            "  special TEXT"
            ")"));
        ok = ok && query.exec(QStringLiteral(
            "CREATE INDEX IF NOT EXISTS bookmarks_parent ON bookmarks(parent_id, position)"));

        if (ok) {
            const QVariant now = QDateTime::currentMSecsSinceEpoch();
            for (const auto &root : {std::make_pair(QStringLiteral("Bookmarks Toolbar"),
                                                    QStringLiteral("toolbar")),
                                     std::make_pair(QStringLiteral("Other Bookmarks"),
                                                    QStringLiteral("other"))}) {
                QSqlQuery insert(m_db);
                insert.prepare(QStringLiteral(
                    "INSERT INTO bookmarks (parent_id, is_folder, title, url, position,"
                    " created_at, special) "
                    "SELECT NULL, 1, ?, NULL, 0, ?, ? "
                    "WHERE NOT EXISTS (SELECT 1 FROM bookmarks WHERE special = ?)"));
                insert.addBindValue(root.first);
                insert.addBindValue(now);
                insert.addBindValue(root.second);
                insert.addBindValue(root.second);
                ok = ok && insert.exec();
            }
        }
    }

    if (!ok) {
        qWarning("Database: migration failed: %s", qPrintable(query.lastError().text()));
        m_db.rollback();
        return;
    }

    // Only bump the version once every statement succeeded.
    if (!query.exec(QStringLiteral("PRAGMA user_version = %1").arg(kSchemaVersion))) {
        qWarning("Database: failed to set user_version: %s",
                 qPrintable(query.lastError().text()));
        m_db.rollback();
        return;
    }

    if (!m_db.commit())
        qWarning("Database: failed to commit migration: %s",
                 qPrintable(m_db.lastError().text()));
}
