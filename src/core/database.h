#pragma once

#include <QSqlDatabase>
#include <QString>

// Shared `Database` block: opens and keeps Kondor's single SQLite file
// (<AppDataLocation>/kondor.sqlite) and applies schema migrations via
// `PRAGMA user_version`. Not exposed to QML — the singletons that persist data
// (HistoryManager, later bookmarks, etc.) talk to it.
class Database
{
public:
    static Database *instance();

    bool isValid() const;
    QSqlDatabase handle() const;

private:
    Database();

    void migrate();
    int schemaVersion() const;

    QSqlDatabase m_db;
    bool m_valid = false;
};
