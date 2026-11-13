#include <QTemporaryFile>
#include <QTest>

#include "passwords/csv/passwordimportfile.h"

class TestPasswordImportFile : public QObject
{
    Q_OBJECT

private slots:
    void rejectsFilesOverTheSizeLimit();
    void rejectsMissingAndRemoteFiles();
    void readsSmallFiles();
};

void TestPasswordImportFile::rejectsFilesOverTheSizeLimit()
{
    QTemporaryFile file;
    QVERIFY(file.open());
    QVERIFY(file.resize(20 * 1024 * 1024 + 1));

    const ImportFile result = readImportFile(QUrl::fromLocalFile(file.fileName()));

    QCOMPARE(result.error, QStringLiteral("tooLarge"));
    QVERIFY(result.data.isEmpty());
}

void TestPasswordImportFile::rejectsMissingAndRemoteFiles()
{
    const QUrl missing = QUrl::fromLocalFile(QStringLiteral("/nonexistent/passwords.csv"));
    const QUrl remote(QStringLiteral("https://example.com/passwords.csv"));

    QCOMPARE(readImportFile(missing).error, QStringLiteral("unreadable"));
    QCOMPARE(readImportFile(remote).error, QStringLiteral("unreadable"));
}

void TestPasswordImportFile::readsSmallFiles()
{
    QTemporaryFile file;
    QVERIFY(file.open());
    file.write("a,b\n");
    file.flush();

    const ImportFile result = readImportFile(QUrl::fromLocalFile(file.fileName()));

    QVERIFY(result.error.isEmpty());
    QCOMPARE(result.data, QByteArray("a,b\n"));
}

QTEST_APPLESS_MAIN(TestPasswordImportFile)
#include "tst_passwordimportfile.moc"
