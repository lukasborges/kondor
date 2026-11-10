#include <QSignalSpy>
#include <QTest>

#include "singleinstance.h"

class TestSingleInstance : public QObject
{
    Q_OBJECT

private slots:
    void encodesAndDecodesMessage();
    void rejectsInvalidData();
    void forwardsMessageToRunningInstance();
    void forwardsWhenAnotherInstanceStartedFirst();
};

void TestSingleInstance::encodesAndDecodesMessage()
{
    SingleInstanceMessage message;
    message.urls = {QUrl(QStringLiteral("https://kde.org")),
                    QUrl::fromLocalFile(QStringLiteral("/tmp/a page.html"))};
    message.privateMode = true;
    message.newWindow = true;
    message.activationToken = QByteArrayLiteral("activation-token");

    const QByteArray encoded = SingleInstance::encodeMessage(message);
    QVERIFY(encoded.endsWith('\n'));
    QCOMPARE(encoded.count('\n'), 1);

    const SingleInstanceMessage decoded = SingleInstance::decodeMessage(encoded);
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
        SingleInstance::decodeMessage(QByteArrayLiteral("not json"));
    QVERIFY(decoded.urls.isEmpty());
    QCOMPARE(decoded.privateMode, false);
    QCOMPARE(decoded.newWindow, false);
    QVERIFY(decoded.activationToken.isEmpty());
}

void TestSingleInstance::forwardsMessageToRunningInstance()
{
    const QString name = QStringLiteral("kondor-test-%1")
                             .arg(QCoreApplication::applicationPid());
    SingleInstance server(name);
    QCOMPARE(server.start(SingleInstanceMessage()),
             SingleInstance::StartResult::Listening);

    QSignalSpy spy(&server, &SingleInstance::messageReceived);

    SingleInstanceMessage outgoing;
    outgoing.urls = {QUrl(QStringLiteral("https://kde.org"))};
    outgoing.privateMode = true;
    outgoing.activationToken = QByteArrayLiteral("token");

    SingleInstance client(name);
    QVERIFY(client.sendMessage(outgoing));
    QVERIFY(spy.wait(2000));
    QCOMPARE(spy.count(), 1);

    const auto received = spy.at(0).at(0).value<SingleInstanceMessage>();
    QCOMPARE(received.urls.size(), 1);
    QCOMPARE(received.urls.at(0), outgoing.urls.at(0));
    QCOMPARE(received.privateMode, true);
    QCOMPARE(received.activationToken, outgoing.activationToken);
}

void TestSingleInstance::forwardsWhenAnotherInstanceStartedFirst()
{
    const QString name = QStringLiteral("kondor-test-race-%1")
                             .arg(QCoreApplication::applicationPid());
    SingleInstance running(name);
    QCOMPARE(running.start(SingleInstanceMessage()),
             SingleInstance::StartResult::Listening);

    QSignalSpy spy(&running, &SingleInstance::messageReceived);

    // The second launch loses listen() and must hand its message over instead
    // of replacing the live socket.
    SingleInstance later(name);
    QCOMPARE(later.start(SingleInstanceMessage()),
             SingleInstance::StartResult::Forwarded);
    QVERIFY(spy.wait(2000));
    QCOMPARE(spy.count(), 1);
}

QTEST_GUILESS_MAIN(TestSingleInstance)
#include "tst_singleinstance.moc"
