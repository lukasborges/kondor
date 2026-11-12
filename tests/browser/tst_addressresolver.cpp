#include <QTest>

#include "browser/addressresolver.h"

class TestAddressResolver : public QObject
{
    Q_OBJECT

private slots:
    void resolvesAddress_data();
    void resolvesAddress();
    void addressUrls_data();
    void addressUrls();
    void searchUrls_data();
    void searchUrls();
};

void TestAddressResolver::resolvesAddress_data()
{
    QTest::addColumn<QString>("input");
    QTest::addColumn<QString>("expected");

    const QString homePage = QStringLiteral("https://home.example/");

    QTest::newRow("empty input uses the home page") << QString() << homePage;
    QTest::newRow("blank input uses the home page") << QStringLiteral("   ") << homePage;
    QTest::newRow("naked domain") << QStringLiteral("kde.org") << QStringLiteral("https://kde.org");
    QTest::newRow("domain with path")
        << QStringLiteral("kde.org/applications") << QStringLiteral("https://kde.org/applications");
    QTest::newRow("explicit scheme")
        << QStringLiteral("http://example.com") << QStringLiteral("http://example.com");
    QTest::newRow("localhost with port")
        << QStringLiteral("localhost:8080") << QStringLiteral("http://localhost:8080");
    QTest::newRow("loopback ip")
        << QStringLiteral("127.0.0.1") << QStringLiteral("http://127.0.0.1");
    QTest::newRow("private 10/8")
        << QStringLiteral("10.0.0.1") << QStringLiteral("http://10.0.0.1");
    QTest::newRow("private 192.168/16")
        << QStringLiteral("192.168.0.1") << QStringLiteral("http://192.168.0.1");
    QTest::newRow("private 172.16/12")
        << QStringLiteral("172.16.0.1") << QStringLiteral("http://172.16.0.1");
    QTest::newRow("public 172.15")
        << QStringLiteral("172.15.0.1") << QStringLiteral("https://172.15.0.1");
    QTest::newRow("public 172.32")
        << QStringLiteral("172.32.0.1") << QStringLiteral("https://172.32.0.1");
    QTest::newRow("public ip")
        << QStringLiteral("8.8.8.8") << QStringLiteral("https://8.8.8.8");
    QTest::newRow("about scheme")
        << QStringLiteral("about:blank") << QStringLiteral("about:blank");
    QTest::newRow("file scheme")
        << QStringLiteral("file:///etc/hosts") << QStringLiteral("file:///etc/hosts");
    QTest::newRow("data scheme")
        << QStringLiteral("data:text/plain,hi") << QStringLiteral("data:text/plain,hi");
    QTest::newRow("single word searches")
        << QStringLiteral("kde") << QStringLiteral("https://duckduckgo.com/?q=kde");
    QTest::newRow("spaces are encoded")
        << QStringLiteral("hello world")
        << QStringLiteral("https://duckduckgo.com/?q=hello%20world");
    QTest::newRow("plus and space are encoded")
        << QStringLiteral("c++ tutorial")
        << QStringLiteral("https://duckduckgo.com/?q=c%2B%2B%20tutorial");
    QTest::newRow("question with a domain searches")
        << QStringLiteral("what is kde.org?")
        << QStringLiteral("https://duckduckgo.com/?q=what%20is%20kde.org%3F");
}

void TestAddressResolver::resolvesAddress()
{
    QFETCH(QString, input);
    QFETCH(QString, expected);

    const QUrl homePage(QStringLiteral("https://home.example/"));
    const QString searchTemplate = QStringLiteral("https://duckduckgo.com/?q=%1");

    const QUrl actual = resolveAddress(input, homePage, searchTemplate);
    QCOMPARE(actual.toString(QUrl::FullyEncoded), expected);
}

void TestAddressResolver::addressUrls_data()
{
    QTest::addColumn<QString>("input");
    QTest::addColumn<QString>("expected");

    QTest::newRow("naked domain") << QStringLiteral("teste.com.br")
                                  << QStringLiteral("https://teste.com.br");
    QTest::newRow("domain with path")
        << QStringLiteral("kde.org/applications") << QStringLiteral("https://kde.org/applications");
    QTest::newRow("explicit scheme")
        << QStringLiteral("http://example.com") << QStringLiteral("http://example.com");
    QTest::newRow("node.js looks like a host")
        << QStringLiteral("node.js") << QStringLiteral("https://node.js");
    QTest::newRow("localhost with port")
        << QStringLiteral("localhost:8080") << QStringLiteral("http://localhost:8080");
    QTest::newRow("about scheme")
        << QStringLiteral("about:blank") << QStringLiteral("about:blank");
    QTest::newRow("plain word is not an address") << QStringLiteral("kde") << QString();
    QTest::newRow("spaces are not an address")
        << QStringLiteral("kde plasma") << QString();
    QTest::newRow("blank input") << QString() << QString();
    QTest::newRow("whitespace input") << QStringLiteral("   ") << QString();
}

void TestAddressResolver::addressUrls()
{
    QFETCH(QString, input);
    QFETCH(QString, expected);

    const QUrl actual = addressUrl(input);
    QCOMPARE(actual.toString(QUrl::FullyEncoded), expected);
}

void TestAddressResolver::searchUrls_data()
{
    QTest::addColumn<QString>("input");
    QTest::addColumn<QString>("expected");

    QTest::newRow("address text still has a search URL")
        << QStringLiteral("teste.com.br")
        << QStringLiteral("https://duckduckgo.com/?q=teste.com.br");
    QTest::newRow("node.js searches too")
        << QStringLiteral("node.js") << QStringLiteral("https://duckduckgo.com/?q=node.js");
    QTest::newRow("plain words")
        << QStringLiteral("kde plasma")
        << QStringLiteral("https://duckduckgo.com/?q=kde%20plasma");
    QTest::newRow("localhost") << QStringLiteral("localhost:8080")
                               << QStringLiteral("https://duckduckgo.com/?q=localhost%3A8080");
    QTest::newRow("blank input") << QString() << QStringLiteral("https://duckduckgo.com/?q=");
}

void TestAddressResolver::searchUrls()
{
    QFETCH(QString, input);
    QFETCH(QString, expected);

    const QString searchTemplate = QStringLiteral("https://duckduckgo.com/?q=%1");

    const QUrl actual = searchUrl(input, searchTemplate);
    QCOMPARE(actual.toString(QUrl::FullyEncoded), expected);
}

QTEST_GUILESS_MAIN(TestAddressResolver)
#include "tst_addressresolver.moc"
