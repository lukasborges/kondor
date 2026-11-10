#include <QTest>

#include "passwords/passwordstore.h"

class TestPasswordStore : public QObject
{
    Q_OBJECT

private slots:
    void originOf_data();
    void originOf();
    void canSaveFor_data();
    void canSaveFor();
    void originFromInput_data();
    void originFromInput();
    void containsWhenClosed();
    void startsClosed();
};

void TestPasswordStore::originOf_data()
{
    QTest::addColumn<QUrl>("url");
    QTest::addColumn<QString>("origin");

    QTest::newRow("https") << QUrl(QStringLiteral("https://Example.com/login?x=1"))
                           << QStringLiteral("https://example.com");
    QTest::newRow("default port dropped") << QUrl(QStringLiteral("https://example.com:443/"))
                                          << QStringLiteral("https://example.com");
    QTest::newRow("custom port kept") << QUrl(QStringLiteral("http://localhost:8080/a"))
                                      << QStringLiteral("http://localhost:8080");
    // location.origin is always punycode, so the key must be too.
    QTest::newRow("idn") << QUrl(QStringLiteral("https://b\u00fccher.example/login"))
                         << QStringLiteral("https://xn--bcher-kva.example");
    QTest::newRow("file") << QUrl(QStringLiteral("file:///tmp/a.html")) << QString();
    QTest::newRow("about") << QUrl(QStringLiteral("about:blank")) << QString();
}

void TestPasswordStore::originOf()
{
    QFETCH(QUrl, url);
    QFETCH(QString, origin);
    QCOMPARE(PasswordStore::originOf(url), origin);
}

void TestPasswordStore::originFromInput_data()
{
    QTest::addColumn<QString>("text");
    QTest::addColumn<QString>("origin");

    const QString example = QStringLiteral("https://example.com");
    QTest::newRow("bare host") << QStringLiteral("example.com") << example;
    QTest::newRow("with path") << QStringLiteral("https://example.com/login") << example;
    QTest::newRow("upper case, default port") << QStringLiteral("https://EXAMPLE.com:443") << example;
    QTest::newRow("trimmed") << QStringLiteral("  example.com \n") << example;
    QTest::newRow("host with path") << QStringLiteral("invent.kde.org/foo")
                                    << QStringLiteral("https://invent.kde.org");
    QTest::newRow("http refused") << QStringLiteral("http://example.com") << QString();
    QTest::newRow("ftp refused") << QStringLiteral("ftp://example.com") << QString();
    QTest::newRow("localhost accepted") << QStringLiteral("http://localhost:8080")
                                        << QStringLiteral("http://localhost:8080");
    QTest::newRow("empty") << QString() << QString();
    QTest::newRow("blank") << QStringLiteral("   ") << QString();
}

void TestPasswordStore::originFromInput()
{
    QFETCH(QString, text);
    QFETCH(QString, origin);
    QCOMPARE(PasswordStore::originFromInput(text), origin);
}

void TestPasswordStore::containsWhenClosed()
{
    QVERIFY(!PasswordStore::instance()->contains(QStringLiteral("https://example.com"),
                                                 QStringLiteral("student")));
}

void TestPasswordStore::canSaveFor_data()
{
    QTest::addColumn<QString>("origin");
    QTest::addColumn<bool>("allowed");

    QTest::newRow("https") << QStringLiteral("https://example.com") << true;
    QTest::newRow("http") << QStringLiteral("http://example.com") << false;
    QTest::newRow("localhost") << QStringLiteral("http://localhost:3000") << true;
    QTest::newRow("subdomain of localhost") << QStringLiteral("http://app.localhost") << true;
    QTest::newRow("empty") << QString() << false;
}

void TestPasswordStore::canSaveFor()
{
    QFETCH(QString, origin);
    QFETCH(bool, allowed);
    QCOMPARE(PasswordStore::canSaveFor(origin), allowed);
}

void TestPasswordStore::startsClosed()
{
    // The wallet is only opened on first use, never at startup.
    PasswordStore *store = PasswordStore::instance();
    QCOMPARE(store->state(), QStringLiteral("closed"));
    QVERIFY(store->entries().isEmpty());
    QVERIFY(store->usernames(QStringLiteral("https://example.com")).isEmpty());
}

QTEST_GUILESS_MAIN(TestPasswordStore)
#include "tst_passwordstore.moc"
