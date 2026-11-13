#include <QDir>
#include <QSignalSpy>
#include <QTest>

#include "app/instance/singleinstance.h"

class TestSingleInstance : public QObject
{
    Q_OBJECT

private slots:
    void socketNameDependsOnProfileDirectory();
    void encodesAndDecodesMessage();
    void rejectsInvalidData();
    void forwardsMessageToRunningInstance();
    void forwardsWhenAnotherInstanceStartedFirst();

private:
    static SingleInstanceMessage privateUrlMessage();
    static void verifyReceived(const SingleInstanceMessage &received,
                               const SingleInstanceMessage &sent);
};

void TestSingleInstance::socketNameDependsOnProfileDirectory()
{
    const QByteArray originalDataHome = qgetenv("XDG_DATA_HOME");
    const QString base = QDir::tempPath() + QStringLiteral("/kondor-socket-test-%1")
                             .arg(QCoreApplication::applicationPid());

    qputenv("XDG_DATA_HOME", (base + QStringLiteral("/first")).toUtf8());
    const QString firstName = SingleInstance::serverName();
    qputenv("XDG_DATA_HOME", (base + QStringLiteral("/second")).toUtf8());
    const QString secondName = SingleInstance::serverName();

    if (originalDataHome.isEmpty())
        qunsetenv("XDG_DATA_HOME");
    else
        qputenv("XDG_DATA_HOME", originalDataHome);

    QVERIFY(firstName.endsWith(QStringLiteral(".socket")));
    QVERIFY(firstName.contains(QStringLiteral("/kondor-")));
    QVERIFY(firstName != secondName);
}

void TestSingleInstance::encodesAndDecodesMessage()
{
    SingleInstanceMessage message;
    message.urls = {QUrl(QStringLiteral("https://kde.org")),
                    QUrl::fromLocalFile(QStringLiteral("/tmp/a page.html"))};
    message.privateMode = true;
    message.newWindow = true;
    message.activationToken = QByteArrayLiteral("activation-token");

    const QByteArray encoded = message.toJsonLine();
    QVERIFY(encoded.endsWith('\n'));
    QCOMPARE(encoded.count('\n'), 1);

    const SingleInstanceMessage decoded = SingleInstanceMessage::fromJsonLine(encoded);
    QCOMPARE(decoded.urls.size(), message.urls.size());
    for (int i = 0; i < message.urls.size(); ++i)
        QCOMPARE(decoded.urls.at(i), message.urls.at(i));
    QCOMPARE(decoded.privateMode, true);
    QCOMPARE(decoded.newWindow, true);
    QCOMPARE(decoded.activationToken, message.activationToken);
}

void TestSingleInstance::rejectsInvalidData()
{
    const SingleInstanceMessage decoded =
        SingleInstanceMessage::fromJsonLine(QByteArrayLiteral("not json"));
    QVERIFY(decoded.urls.isEmpty());
    QCOMPARE(decoded.privateMode, false);
    QCOMPARE(decoded.newWindow, false);
    QVERIFY(decoded.activationToken.isEmpty());
}

SingleInstanceMessage TestSingleInstance::privateUrlMessage()
{
    SingleInstanceMessage message;
    message.urls = {QUrl(QStringLiteral("https://kde.org"))};
    message.privateMode = true;
    message.activationToken = QByteArrayLiteral("token");
    return message;
}

void TestSingleInstance::verifyReceived(const SingleInstanceMessage &received,
                                        const SingleInstanceMessage &sent)
{
    QCOMPARE(received.urls.size(), 1);
    QCOMPARE(received.urls.at(0), sent.urls.at(0));
    QCOMPARE(received.privateMode, true);
    QCOMPARE(received.activationToken, sent.activationToken);
}

void TestSingleInstance::forwardsMessageToRunningInstance()
{
    const QString name = QStringLiteral("kondor-test-%1")
                             .arg(QCoreApplication::applicationPid());
    SingleInstance server(name);
    QCOMPARE(server.start(SingleInstanceMessage()),
             SingleInstance::StartResult::Listening);
    QSignalSpy spy(&server, &SingleInstance::messageReceived);

    const SingleInstanceMessage outgoing = privateUrlMessage();
    SingleInstance client(name);
    QVERIFY(client.sendMessage(outgoing));
    QVERIFY(spy.wait(2000));
    QCOMPARE(spy.count(), 1);
    verifyReceived(spy.at(0).at(0).value<SingleInstanceMessage>(), outgoing);
}

void TestSingleInstance::forwardsWhenAnotherInstanceStartedFirst()
{
    const QString name = QStringLiteral("kondor-test-race-%1")
                             .arg(QCoreApplication::applicationPid());
    SingleInstance running(name);
    QCOMPARE(running.start(SingleInstanceMessage()),
             SingleInstance::StartResult::Listening);

    QSignalSpy spy(&running, &SingleInstance::messageReceived);

    SingleInstance later(name);
    QCOMPARE(later.start(SingleInstanceMessage()),
             SingleInstance::StartResult::Forwarded);
    QVERIFY(spy.wait(2000));
    QCOMPARE(spy.count(), 1);
}

QTEST_GUILESS_MAIN(TestSingleInstance)
#include "tst_singleinstance.moc"
