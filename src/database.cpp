#include "database.h"

#include <QCoreApplication>
#include <QDir>
#include <QDateTime>
#include <QSqlError>
#include <QSqlQuery>
#include <QStandardPaths>
#include <QString>
#include <QVariant>
#include <QVector>
#include <functional>
#include <utility>

namespace {
// Schema version. Each migration bumps `PRAGMA user_version` by 1.
constexpr int kSchemaVersion = 5;

// One node of the bookmark set a new profile starts with. Folders have no URL
// and their title is translated at insert time; bookmark titles are site names
// and stay as written.
struct DefaultBookmark {
    const char *title;
    const char *url;
    QVector<DefaultBookmark> children;

    bool isFolder() const { return url == nullptr; }
};

const QVector<DefaultBookmark> &defaultBookmarks()
{
    static const QVector<DefaultBookmark> bookmarks = {
        {"KDE", "https://kde.org/", {}},
        {"Planet KDE", "https://planet.kde.org/", {}},
        {"Qt Docs", "https://doc.qt.io/", {}},
        {QT_TRANSLATE_NOOP("DefaultBookmarks", "News"), nullptr,
         {
             {"LWN.net", "https://lwn.net/", {}},
             {"Phoronix", "https://www.phoronix.com/", {}},
             {"9to5Linux", "https://9to5linux.com/", {}},
             {"OMG! Ubuntu", "https://www.omgubuntu.co.uk/", {}},
             {"GamingOnLinux", "https://www.gamingonlinux.com/", {}},
             {"DistroWatch", "https://distrowatch.com/", {}},
         }},
        {QT_TRANSLATE_NOOP("DefaultBookmarks", "Development"), nullptr,
         {
             {"KDE Developer", "https://develop.kde.org/", {}},
             {"KDE Human Interface Guidelines", "https://develop.kde.org/hig/", {}},
             {"KDE Invent", "https://invent.kde.org/", {}},
             {"freedesktop.org", "https://www.freedesktop.org/", {}},
             {"The Linux Kernel Archives", "https://www.kernel.org/", {}},
             {"Kondor Browser on GitHub", "https://github.com/lukasborges/kondor", {}},
         }},
        {QT_TRANSLATE_NOOP("DefaultBookmarks", "Linux"), nullptr,
         {
             {"Fedora Project", "https://fedoraproject.org/", {}},
             {"Fedora Docs", "https://docs.fedoraproject.org/", {}},
             {"ArchWiki", "https://wiki.archlinux.org/", {}},
             {"Flathub", "https://flathub.org/", {}},
             {"KDE Applications", "https://apps.kde.org/", {}},
             {"KDE UserBase", "https://userbase.kde.org/", {}},
             {"KDE Discuss", "https://discuss.kde.org/", {}},
         }},
    };
    return bookmarks;
}

// Fills the empty Bookmarks Toolbar with the default set. Only a profile
// without any user bookmark or folder (special IS NULL) gets them, so existing
// profiles are never touched.
bool seedDefaultBookmarks(const QSqlDatabase &db)
{
    QSqlQuery existing(db);
    if (!existing.exec(QStringLiteral("SELECT 1 FROM bookmarks WHERE special IS NULL LIMIT 1")))
        return false;
    if (existing.next())
        return true;

    QSqlQuery toolbar(db);
    if (!toolbar.exec(QStringLiteral("SELECT id FROM bookmarks WHERE special = 'toolbar' LIMIT 1"))
        || !toolbar.next()) {
        return false;
    }
    const QVariant toolbarId = toolbar.value(0);
    const QVariant now = QDateTime::currentMSecsSinceEpoch();

    std::function<bool(const QVector<DefaultBookmark> &, const QVariant &)> insertRows;
    insertRows = [&](const QVector<DefaultBookmark> &rows, const QVariant &parentId) {
        for (int position = 0; position < rows.size(); ++position) {
            const DefaultBookmark &row = rows.at(position);
            QSqlQuery insert(db);
            insert.prepare(QStringLiteral(
                "INSERT INTO bookmarks (parent_id, is_folder, title, url, position,"
                " created_at, special) "
                "VALUES (?, ?, ?, ?, ?, ?, NULL)"));
            const QString title = row.isFolder()
                ? QCoreApplication::translate("DefaultBookmarks", row.title)
                : QString::fromUtf8(row.title);
            insert.addBindValue(parentId);
            insert.addBindValue(row.isFolder() ? 1 : 0);
            insert.addBindValue(title);
            insert.addBindValue(row.isFolder() ? QVariant()
                                               : QVariant(QString::fromUtf8(row.url)));
            insert.addBindValue(position);
            insert.addBindValue(now);
            if (!insert.exec())
                return false;
            if (!row.children.isEmpty()
                && !insertRows(row.children, insert.lastInsertId())) {
                return false;
            }
        }
        return true;
    };
    return insertRows(defaultBookmarks(), toolbarId);
}
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

    if (current < 3) {
        // One favicon per host, filled by normal tabs only (FaviconStore).
        ok = ok && query.exec(QStringLiteral(
            "CREATE TABLE IF NOT EXISTS favicons ("
            "  host TEXT PRIMARY KEY,"
            "  image BLOB NOT NULL,"
            "  updated_at INTEGER NOT NULL"
            ")"));
    }

    if (current < 4) {
        // Default bookmarks for a new profile. It only fills a Bookmarks
        // Toolbar that has no user bookmark, and never runs again once the
        // version is bumped, so deleted defaults never come back.
        ok = ok && seedDefaultBookmarks(m_db);
    }

    if (current < 5) {
        // Storage of the Kondor extensions (JSON values, see ExtensionManager).
        ok = ok && query.exec(QStringLiteral(
            "CREATE TABLE IF NOT EXISTS extension_storage ("
            "  extension_id TEXT NOT NULL,"
            "  key TEXT NOT NULL,"
            "  value TEXT NOT NULL,"
            "  PRIMARY KEY (extension_id, key)"
            ")"));
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
