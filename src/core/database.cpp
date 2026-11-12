#include "core/database.h"

#include "core/databasemigrations.h"
#include "core/sql.h"

#include <QDir>
#include <QSqlError>
#include <QSqlQuery>
#include <QStandardPaths>
#include <functional>

namespace {

constexpr int kSchemaVersion = 5;

struct MigrationStep {
    int version;
    std::function<bool()> apply;
};

const QList<MigrationStep> &migrationSteps()
{
    static const QList<MigrationStep> steps = {
        {1, DatabaseMigrations::createHistoryTable},
        {2, DatabaseMigrations::createBookmarksTable},
        {2, DatabaseMigrations::createRootFolders},
        {3, DatabaseMigrations::createFaviconsTable},
        {4, DatabaseMigrations::seedDefaultBookmarks},
        {5, DatabaseMigrations::createExtensionStorageTable},
    };
    return steps;
}

}

Database *Database::instance()
{
    static Database *db = nullptr;
    if (!db) {
        db = new Database;
        db->open();
    }
    return db;
}

Database::Database()
{
    const QString dir = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation);
    QDir().mkpath(dir);
    m_path = dir + QStringLiteral("/kondor.sqlite");
    m_db = QSqlDatabase::addDatabase(QStringLiteral("QSQLITE"), QStringLiteral("kondor"));
    m_db.setDatabaseName(m_path);
}

void Database::open()
{
    if (!m_db.open()) {
        qWarning("Database: failed to open %s: %s", qPrintable(m_path),
                 qPrintable(m_db.lastError().text()));
        return;
    }
    m_valid = isUsableFile();
    if (!m_valid)
        m_db.close();
    else
        migrate();
}

bool Database::isUsableFile() const
{
    QSqlQuery probe(m_db);
    if (probe.exec(QStringLiteral("PRAGMA user_version")))
        return true;
    qWarning("Database: %s is not a usable SQLite database: %s", qPrintable(m_path),
             qPrintable(m_db.lastError().text()));
    return false;
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
    auto query = Sql::run(QStringLiteral("PRAGMA user_version"));
    return query && query->next() ? query->value(0).toInt() : 0;
}

void Database::migrate()
{
    const int current = schemaVersion();
    if (current >= kSchemaVersion)
        return;
    if (!Sql::inTransaction([&] { return applyMigrations(current); }))
        qWarning("Database: migration failed: %s", qPrintable(m_db.lastError().text()));
}

bool Database::applyMigrations(int currentVersion)
{
    for (const MigrationStep &step : migrationSteps()) {
        if (step.version > currentVersion && !step.apply())
            return false;
    }
    return Sql::run(QStringLiteral("PRAGMA user_version = %1").arg(kSchemaVersion)).has_value();
}
