#include <QFile>
#include <QTest>

#include "passwords/passwordimport.h"

using namespace PasswordImport;

class TestPasswordImport : public QObject
{
    Q_OBJECT

private slots:
    void fixtures_data();
    void fixtures();
    void quotedFields();
    void crlfAndBom();
    void shortRows();
    void bitwardenTwoUris();
    void websiteColumn();
    void skipsAndDuplicates();
    void notAPasswordExport();
    void emptyFile();

private:
    static QByteArray fixture(const QString &name)
    {
        QFile file(QStringLiteral(KONDOR_TEST_DATA_DIR "/passwords/") + name);
        if (!file.open(QIODevice::ReadOnly))
            return {};
        return file.readAll();
    }
};

void TestPasswordImport::fixtures_data()
{
    QTest::addColumn<QString>("file");
    QTest::addColumn<int>("format");
    QTest::addColumn<int>("count");
    QTest::addColumn<QString>("firstUser");
    QTest::addColumn<QString>("firstPassword");

    QTest::newRow("chrome") << "chrome.csv" << int(Format::Chrome) << 2 << "alice" << "pw-chrome-1";
    QTest::newRow("firefox") << "firefox.csv" << int(Format::Firefox) << 2 << "alice" << "pw-fx-1";
    QTest::newRow("bitwarden") << "bitwarden.csv" << int(Format::Bitwarden) << 2 << "alice" << "pw-bw-1";
    QTest::newRow("1password") << "1password.csv" << int(Format::OnePassword) << 2 << "alice" << "pw-op-1";
    QTest::newRow("keepassxc") << "keepassxc.csv" << int(Format::KeePassXC) << 1 << "alice" << "pw-kp-1";
    QTest::newRow("lastpass") << "lastpass.csv" << int(Format::Csv) << 1 << "alice" << "pw-lp-1";
}

void TestPasswordImport::fixtures()
{
    QFETCH(QString, file);
    QFETCH(int, format);
    QFETCH(int, count);
    QFETCH(QString, firstUser);
    QFETCH(QString, firstPassword);

    const QByteArray data = fixture(file);
    QVERIFY(!data.isEmpty());
    const Result result = parse(data);
    QCOMPARE(result.error, Error::None);
    QCOMPARE(int(result.format), format);
    QCOMPARE(result.logins.size(), count);
    QCOMPARE(result.logins.first().origin, QStringLiteral("https://example.com"));
    QCOMPARE(result.logins.first().username, firstUser);
    QCOMPARE(result.logins.first().password, firstPassword);
}

void TestPasswordImport::quotedFields()
{
    const Result result = parse(
        "url,username,password\n"
        "https://example.com,\"a,b\",\"pa\"\"ss\nword\"\n");
    QCOMPARE(result.logins.size(), 1);
    QCOMPARE(result.logins.first().username, QStringLiteral("a,b"));
    QCOMPARE(result.logins.first().password, QStringLiteral("pa\"ss\nword"));
}

void TestPasswordImport::crlfAndBom()
{
    const Result result = parse(
        "\xEF\xBB\xBF" "url,username,password\r\n"
        "\r\n"
        "https://example.com,alice,one\r\n"
        "https://example.org,bob,two\r\n");
    QCOMPARE(result.error, Error::None);
    QCOMPARE(result.logins.size(), 2);
    QCOMPARE(result.logins.last().password, QStringLiteral("two"));
}

void TestPasswordImport::shortRows()
{
    const Result result = parse(
        "url,username,password,extra\n"
        "https://example.com,alice\n"
        "https://example.org,bob,secret\n");
    QCOMPARE(result.logins.size(), 1);
    QCOMPARE(result.skippedNoCredentials, 1);
}

void TestPasswordImport::bitwardenTwoUris()
{
    const Result result = parse(fixture(QStringLiteral("bitwarden.csv")));
    QCOMPARE(result.logins.size(), 2);
    QCOMPARE(result.logins.at(0).origin, QStringLiteral("https://example.com"));
    QCOMPARE(result.logins.at(1).origin, QStringLiteral("https://www.example.com"));
    QCOMPARE(result.logins.at(1).username, QStringLiteral("alice"));
}

void TestPasswordImport::websiteColumn()
{
    const Result result = parse(
        "url,username,password\n"
        "http://localhost:8080,a,1\n"
        "http://example.com,b,2\n"
        "android://abc@com.example.app,c,3\n"
        "example.com,d,4\n"
        ",e,5\n");
    QCOMPARE(result.logins.size(), 2);
    QCOMPARE(result.logins.at(0).origin, QStringLiteral("http://localhost:8080"));
    QCOMPARE(result.logins.at(1).origin, QStringLiteral("https://example.com"));
    QCOMPARE(result.skippedNoSite, 3);
}

void TestPasswordImport::skipsAndDuplicates()
{
    const Result bitwarden = parse(fixture(QStringLiteral("bitwarden.csv")));
    QCOMPARE(bitwarden.skippedNotLogin, 1);
    QCOMPARE(bitwarden.skippedNoSite, 2);
    QCOMPARE(bitwarden.skippedNoCredentials, 1);

    const Result dup = parse(
        "url,username,password\n"
        "https://example.com,alice,old\n"
        "https://example.com,alice,new\n");
    QCOMPARE(dup.logins.size(), 1);
    QCOMPARE(dup.logins.first().password, QStringLiteral("new"));
}

void TestPasswordImport::notAPasswordExport()
{
    QCOMPARE(parse("name,notes\nfoo,bar\n").error, Error::NotPasswordExport);
}

void TestPasswordImport::emptyFile()
{
    QCOMPARE(parse("url,username,password\n").error, Error::Empty);
    QCOMPARE(parse("").error, Error::Empty);
}

QTEST_APPLESS_MAIN(TestPasswordImport)
#include "tst_passwordimport.moc"
