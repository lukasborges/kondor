#include <QQuickWebEngineProfile>

#include "bridgeharness.h"

class TestExtensionBridgeTabs : public QObject
{
    Q_OBJECT

private slots:
    void init();
    void cleanup();
    void privateBridgeReadsButCannotWrite();
    void privateBridgeRefusedWhenNotAllowed();
    void tabCommandsEmitSignals();
    void tabOpenAcceptsOnlyWebAddresses();
    void unknownMethodIsRefused();
    void toolbarItemCheckedStateIsPerTab();

private:
    QTemporaryDir m_work;
    BridgeFixture m_fixture;
};

void TestExtensionBridgeTabs::init()
{
    QVERIFY(m_work.isValid());
    QVERIFY(installSample(m_work.path()));
    allowInPrivateWindows(QStringLiteral("sample"));
    m_fixture.create();
}

void TestExtensionBridgeTabs::cleanup()
{
    m_fixture.destroy();
    removeEveryExtension();
}

void TestExtensionBridgeTabs::privateBridgeReadsButCannotWrite()
{
    QQuickWebEngineProfile privateProfile;
    QVERIFY(privateProfile.isOffTheRecord());
    Tab privateTab(&privateProfile);
    QVERIFY(privateTab.isPrivate());
    ExtensionBridge privateBridge;
    privateBridge.setTab(&privateTab);
    const QString token = sampleToken();
    const BridgeClient privateClient{&privateBridge, QStringLiteral("sample"), token};

    QVERIFY(m_fixture.client().isOk(QStringLiteral("storage.set"), {QStringLiteral("k"), 42}));
    const QJsonObject read = privateClient.call(QStringLiteral("storage.get"), {QStringLiteral("k")});
    QVERIFY(read.value(QStringLiteral("ok")).toBool());
    QCOMPARE(read.value(QStringLiteral("value")).toInt(), 42);

    const QJsonObject write = privateClient.call(QStringLiteral("storage.set"), {QStringLiteral("k"), 1});
    QVERIFY(!write.value(QStringLiteral("ok")).toBool());
    QCOMPARE(errorOf(write), QStringLiteral("Storage is read-only in private windows"));
    QVERIFY(!privateClient.isOk(QStringLiteral("storage.remove"), {QStringLiteral("k")}));
    QCOMPARE(ExtensionStorage::value(QStringLiteral("sample"), QStringLiteral("k")).toInt(), 42);
}

void TestExtensionBridgeTabs::privateBridgeRefusedWhenNotAllowed()
{
    QQuickWebEngineProfile privateProfile;
    Tab privateTab(&privateProfile);
    ExtensionBridge privateBridge;
    privateBridge.setTab(&privateTab);
    const BridgeClient privateClient{&privateBridge, QStringLiteral("sample"), sampleToken()};

    ExtensionManager::instance()->applyConfiguration(QStringLiteral("sample"), {});
    QVERIFY(!privateClient.isOk(QStringLiteral("storage.get"), {QStringLiteral("k")}));
    QVERIFY(m_fixture.client().isOk(QStringLiteral("storage.get"), {QStringLiteral("k")}));
}

void TestExtensionBridgeTabs::tabCommandsEmitSignals()
{
    const BridgeClient client = m_fixture.client();
    QSignalSpy closes(m_fixture.tab.get(), &Tab::closeRequested);
    QSignalSpy neighbors(m_fixture.tab.get(), &Tab::neighborTabRequested);
    QSignalSpy reloads(m_fixture.tab.get(), &Tab::reloadRequested);

    QVERIFY(client.isOk(QStringLiteral("tabs.close")));
    QCOMPARE(closes.count(), 1);
    QVERIFY(client.isOk(QStringLiteral("tabs.reload")));
    QCOMPARE(reloads.count(), 1);
    QVERIFY(client.isOk(QStringLiteral("tabs.next")));
    QVERIFY(client.isOk(QStringLiteral("tabs.previous")));
    QCOMPARE(neighbors.count(), 2);
    QCOMPARE(neighbors.at(0).at(0).toInt(), 1);
    QCOMPARE(neighbors.at(1).at(0).toInt(), -1);
}

void TestExtensionBridgeTabs::tabOpenAcceptsOnlyWebAddresses()
{
    const BridgeClient client = m_fixture.client();
    QSignalSpy opens(m_fixture.tab.get(), &Tab::openTabRequested);

    QVERIFY(client.isOk(QStringLiteral("tabs.open"), {QStringLiteral("https://example.com/"), true}));
    QCOMPARE(opens.count(), 1);
    QCOMPARE(opens.first().at(0).toUrl(), QUrl(QStringLiteral("https://example.com/")));
    QVERIFY(opens.first().at(1).toBool());
    QVERIFY(!client.isOk(QStringLiteral("tabs.open"), {QStringLiteral("file:///etc/passwd"), false}));
    QVERIFY(!client.isOk(QStringLiteral("tabs.open"), {QStringLiteral("javascript:alert(1)"), false}));
    QCOMPARE(opens.count(), 1);
}

void TestExtensionBridgeTabs::unknownMethodIsRefused()
{
    QVERIFY(!m_fixture.client().isOk(QStringLiteral("no.such.method")));
}

void TestExtensionBridgeTabs::toolbarItemCheckedStateIsPerTab()
{
    const QString id = QStringLiteral("sample");
    QVERIFY(m_fixture.client().isOk(QStringLiteral("action.setChecked"), {QStringLiteral("toggle"), true}));
    TabExtensionItems *items = m_fixture.tab->extensionItems();
    QVERIFY(items->isChecked(id, QStringLiteral("toggle")));
    Tab other(nullptr);
    QVERIFY(!other.extensionItems()->isChecked(id, QStringLiteral("toggle")));
    QSignalSpy triggered(items, &TabExtensionItems::triggered);
    items->trigger(id, QStringLiteral("toggle"), true);
    QVERIFY(!items->isChecked(id, QStringLiteral("toggle")));
    QCOMPARE(triggered.count(), 1);
    QVERIFY(!triggered.first().at(2).toBool());
}

int runTestExtensionBridgeTabs(int argc, char *argv[])
{
    TestExtensionBridgeTabs test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensionbridgetabs.moc"
