#include <QTest>

#include "passwords/import/importoutcome.h"

class TestPasswordImportOutcome : public QObject
{
    Q_OBJECT

private slots:
    void isNotifiedOnceWhenThePageIsClosed();
    void isNotNotifiedWhenThePageIsOpen();
    void isTakenOnce();
};

void TestPasswordImportOutcome::isNotifiedOnceWhenThePageIsClosed()
{
    ImportOutcome outcome;
    outcome.record(5, QStringLiteral("logins.csv"));

    QCOMPARE(outcome.claimNotification().value("count").toInt(), 5);
    QVERIFY(outcome.claimNotification().isEmpty());
    QCOMPARE(outcome.take().value("fileName").toString(), QStringLiteral("logins.csv"));
}

void TestPasswordImportOutcome::isNotNotifiedWhenThePageIsOpen()
{
    ImportOutcome outcome;
    outcome.setPageOpen(true);
    outcome.record(5, QStringLiteral("logins.csv"));

    QVERIFY(outcome.claimNotification().isEmpty());
}

void TestPasswordImportOutcome::isTakenOnce()
{
    ImportOutcome outcome;
    outcome.record(-1, QStringLiteral("logins.csv"));

    QVERIFY(outcome.claimNotification().isEmpty());
    QCOMPARE(outcome.take().value("count").toInt(), -1);
    QVERIFY(outcome.take().isEmpty());
}

QTEST_MAIN(TestPasswordImportOutcome)
#include "tst_passwordimportoutcome.moc"
