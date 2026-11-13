#include <QSignalSpy>
#include <QTemporaryFile>
#include <QTest>

#include "passwords/import/importcommit.h"
#include "passwords/import/importpreparation.h"

using PasswordImport::Login;

namespace {

const QString kSiteA = QStringLiteral("https://a.example");
const QString kSiteB = QStringLiteral("https://b.example");

PendingImport twoSites()
{
    return {{{kSiteA, "ann", "pw1"}, {kSiteB, "bob", "pw2"}, {kSiteB, "cy", "pw3"}}, {}};
}

QUrl csvFile(QTemporaryFile &file)
{
    file.write("url,username,password\nhttps://a.example,ann,pw1\nhttps://b.example,bob,pw2\n");
    file.flush();
    return QUrl::fromLocalFile(file.fileName());
}

ImportPreparation::SavedLoginsSource emptyWallet()
{
    return [] { return std::optional<SavedLogins>(SavedLogins()); };
}

}

class TestPasswordImportAsync : public QObject
{
    Q_OBJECT

private slots:
    void reportsProgressPerOrigin();
    void countsWrittenLogins();
    void failsWhenTheWalletRejectsAWrite();
    void writesNothingForIdenticalLogins();
    void prepareReturnsBeforeTheFileIsParsed();
    void prepareDescribesTheFile();
    void prepareFailsWhenTheWalletIsUnavailable();
    void cancelDropsThePreparedLogins();
    void cancelWhileReadingEmitsNothing();
};

void TestPasswordImportAsync::reportsProgressPerOrigin()
{
    ImportCommit commit(twoSites(), [](const QString &, const QMap<QString, QString> &) { return true; });
    QSignalSpy progressed(&commit, &ImportCommit::progressed);
    QSignalSpy finished(&commit, &ImportCommit::finished);
    QCOMPARE(commit.total(), 2);

    commit.start();
    QCOMPARE(commit.done(), 0);
    QVERIFY(finished.wait());

    QCOMPARE(progressed.count(), 2);
    QCOMPARE(commit.done(), 2);
}

void TestPasswordImportAsync::countsWrittenLogins()
{
    ImportCommit commit(twoSites(), [](const QString &, const QMap<QString, QString> &) { return true; });
    QSignalSpy finished(&commit, &ImportCommit::finished);

    commit.start();

    QVERIFY(finished.wait());
    QCOMPARE(finished.takeFirst().at(0).toInt(), 3);
}

void TestPasswordImportAsync::failsWhenTheWalletRejectsAWrite()
{
    ImportCommit commit(twoSites(), [](const QString &, const QMap<QString, QString> &) { return false; });
    QSignalSpy finished(&commit, &ImportCommit::finished);

    commit.start();

    QVERIFY(finished.wait());
    QCOMPARE(finished.takeFirst().at(0).toInt(), -1);
}

void TestPasswordImportAsync::writesNothingForIdenticalLogins()
{
    PendingImport pending{{{kSiteA, "ann", "pw1"}}, {{kSiteA, {{"ann", "pw1"}}}}};
    int writes = 0;
    ImportCommit commit(pending, [&writes](const QString &, const QMap<QString, QString> &) {
        ++writes;
        return true;
    });
    QSignalSpy finished(&commit, &ImportCommit::finished);

    commit.start();

    QVERIFY(finished.wait());
    QCOMPARE(writes, 0);
    QCOMPARE(finished.takeFirst().at(0).toInt(), 0);
}

void TestPasswordImportAsync::prepareReturnsBeforeTheFileIsParsed()
{
    QTemporaryFile file;
    QVERIFY(file.open());
    ImportPreparation preparation(emptyWallet());
    QSignalSpy prepared(&preparation, &ImportPreparation::prepared);

    preparation.start(csvFile(file));

    QCOMPARE(prepared.count(), 0);
    QVERIFY(preparation.isRunning());
    QVERIFY(prepared.wait());
    QVERIFY(!preparation.isRunning());
}

void TestPasswordImportAsync::prepareDescribesTheFile()
{
    QTemporaryFile file;
    QVERIFY(file.open());
    ImportPreparation preparation(emptyWallet());
    QSignalSpy prepared(&preparation, &ImportPreparation::prepared);

    preparation.start(csvFile(file));

    QVERIFY(prepared.wait());
    const QVariantMap info = prepared.takeFirst().at(0).toMap();
    QCOMPARE(info.value("error").toString(), QString());
    QCOMPARE(info.value("newCount").toInt(), 2);
    QCOMPARE(preparation.takePending().logins.size(), 2);
}

void TestPasswordImportAsync::prepareFailsWhenTheWalletIsUnavailable()
{
    QTemporaryFile file;
    QVERIFY(file.open());
    ImportPreparation preparation([] { return std::optional<SavedLogins>(); });
    QSignalSpy prepared(&preparation, &ImportPreparation::prepared);

    preparation.start(csvFile(file));

    QVERIFY(prepared.wait());
    QCOMPARE(prepared.takeFirst().at(0).toMap().value("error").toString(), QStringLiteral("walletUnavailable"));
    QVERIFY(preparation.takePending().logins.isEmpty());
}

void TestPasswordImportAsync::cancelDropsThePreparedLogins()
{
    QTemporaryFile file;
    QVERIFY(file.open());
    ImportPreparation preparation(emptyWallet());
    QSignalSpy prepared(&preparation, &ImportPreparation::prepared);
    preparation.start(csvFile(file));
    QVERIFY(prepared.wait());

    preparation.cancel();

    QVERIFY(preparation.takePending().logins.isEmpty());
}

void TestPasswordImportAsync::cancelWhileReadingEmitsNothing()
{
    QTemporaryFile file;
    QVERIFY(file.open());
    ImportPreparation preparation(emptyWallet());
    QSignalSpy prepared(&preparation, &ImportPreparation::prepared);
    preparation.start(csvFile(file));

    preparation.cancel();

    QVERIFY(!prepared.wait(300));
    QVERIFY(!preparation.isRunning());
}

QTEST_MAIN(TestPasswordImportAsync)
#include "tst_passwordimportasync.moc"
