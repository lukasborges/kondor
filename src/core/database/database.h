#pragma once

#include <QSqlDatabase>
#include <QString>

class Database
{
public:
    static Database *instance();

    bool isValid() const;
    QSqlDatabase handle() const;

private:
    Database();

    void open();
    bool isUsableFile() const;
    void migrate();
    bool applyMigrations(int currentVersion);
    int schemaVersion() const;

    QSqlDatabase m_db;
    QString m_path;
    bool m_valid = false;
};
