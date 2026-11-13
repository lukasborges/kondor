#include <QTest>

#include "passwords/csv/passwordimportplan.h"

using PasswordImport::Login;

class TestPasswordImportPlan : public QObject
{
    Q_OBJECT

private slots:
    void countsNewIdenticalAndConflictingLogins();
    void countsEachConflictingSiteOnce();
    void mergeKeepsConflictsUnlessReplacing();
    void mergeLeavesIdenticalLoginsUnchanged();
};

namespace {

const QString kSite = QStringLiteral("https://example.com");

SavedLogins savedWith(const QString &origin, const QMap<QString, QString> &logins)
{
    SavedLogins saved;
    saved.insert(origin, logins);
    return saved;
}

}

void TestPasswordImportPlan::countsNewIdenticalAndConflictingLogins()
{
    const SavedLogins saved = savedWith(kSite, {{"same", "pw"}, {"other", "old"}});
    const QList<Login> logins{{kSite, "fresh", "pw"}, {kSite, "same", "pw"}, {kSite, "other", "new"}};

    const ImportSummary summary = summarizeImport(logins, saved);

    QCOMPARE(summary.newCount, 1);
    QCOMPARE(summary.identicalCount, 1);
    QCOMPARE(summary.conflictCount, 1);
}

void TestPasswordImportPlan::countsEachConflictingSiteOnce()
{
    const SavedLogins saved = savedWith(kSite, {{"a", "old"}, {"b", "old"}});
    const QList<Login> logins{{kSite, "a", "new"}, {kSite, "b", "new"}};

    const ImportSummary summary = summarizeImport(logins, saved);

    QCOMPARE(summary.conflictCount, 2);
    QCOMPARE(summary.conflictSites, 1);
}

void TestPasswordImportPlan::mergeKeepsConflictsUnlessReplacing()
{
    QMap<QString, QString> saved{{"a", "old"}};
    const QList<Login> logins{{kSite, "a", "new"}, {kSite, "b", "pw"}};

    QCOMPARE(mergeLogins(saved, logins, false), 1);
    QCOMPARE(saved.value("a"), QStringLiteral("old"));
    QCOMPARE(mergeLogins(saved, logins, true), 1);
    QCOMPARE(saved.value("a"), QStringLiteral("new"));
}

void TestPasswordImportPlan::mergeLeavesIdenticalLoginsUnchanged()
{
    QMap<QString, QString> saved{{"a", "pw"}};

    QCOMPARE(mergeLogins(saved, {{kSite, "a", "pw"}}, true), 0);
    QCOMPARE(saved.size(), 1);
}

QTEST_APPLESS_MAIN(TestPasswordImportPlan)
#include "tst_passwordimportplan.moc"
