#pragma once

#include <QDateTime>
#include <QSqlQuery>
#include <QTest>
#include <QVariantMap>

#include "core/database.h"
#include "core/settings.h"
#include "history/historymanager.h"

inline void resetHistory()
{
    QVERIFY(Database::instance()->isValid());
    QSqlQuery clear(Database::instance()->handle());
    QVERIFY(clear.exec(QStringLiteral("DELETE FROM history")));
    Settings::instance()->setHiddenTopSites({});
}

inline void addVisit(const QString &url, const QString &title, qint64 visitedAt)
{
    QSqlQuery insert(Database::instance()->handle());
    insert.prepare(QStringLiteral("INSERT INTO history (url, title, visited_at) VALUES (?, ?, ?)"));
    insert.addBindValue(url);
    insert.addBindValue(title);
    insert.addBindValue(visitedAt);
    QVERIFY(insert.exec());
}

inline QString fieldOf(const QVariant &row, const char *key)
{
    return row.toMap().value(QLatin1String(key)).toString();
}

inline void addGroupedVisits()
{
    const qint64 now = QDateTime::currentMSecsSinceEpoch();
    addVisit(QStringLiteral("https://kde.org/a"), QStringLiteral("A"), now - 4000);
    addVisit(QStringLiteral("https://kde.org/b"), QStringLiteral("B"), now - 3000);
    addVisit(QStringLiteral("https://kde.org/a"), QStringLiteral("A latest"), now - 2000);
    addVisit(QStringLiteral("https://wikipedia.org/"), QStringLiteral("Wiki"), now - 5000);
    addVisit(QStringLiteral("https://fedoraproject.org/"), QStringLiteral("Fedora"), now - 6000);
}

int runTestHistorySuggestions(int argc, char *argv[]);
