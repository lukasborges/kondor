#include "bridgeharness.h"

class TestExtensionBridge : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void init();
    void cleanup();
    void storageQuota();
    void storageIsPerExtension();
    void bridgeRejectsWrongToken();
    void bridgeRefusesDownloadWithoutPermission();
    void bridgeRefusesTabsWithoutPermission();
    void bridgeOffExtension();

private:
    void installSampleWithoutTabsPermission();

    QTemporaryDir m_work;
    BridgeFixture m_fixture;
};

void TestExtensionBridge::initTestCase()
{
    QVERIFY(m_work.isValid());
}

void TestExtensionBridge::init()
{
    QVERIFY(installSample(m_work.path()));
    m_fixture.create();
}

void TestExtensionBridge::cleanup()
{
    m_fixture.destroy();
    removeEveryExtension();
}

void TestExtensionBridge::storageQuota()
{
    const QString id = QStringLiteral("sample");
    QVERIFY(ExtensionStorage::setValue(id, QStringLiteral("a"), QJsonValue(QString(600 * 1024, QLatin1Char('x')))).isWritten);
    const QString error = ExtensionStorage::setValue(id, QStringLiteral("b"), QJsonValue(QString(600 * 1024, QLatin1Char('y')))).error;
    QVERIFY(error.contains(QLatin1String("full")));
    QVERIFY(!ExtensionStorage::keys(id).contains(QStringLiteral("b")));
    QVERIFY(ExtensionStorage::setValue(id, QStringLiteral("a"), QJsonValue(QString(900 * 1024, QLatin1Char('z')))).isWritten);
    ExtensionStorage::removeValue(id, QStringLiteral("a"));
    const QJsonObject object{{QStringLiteral("n"), 1}, {QStringLiteral("list"), QJsonArray{1, 2}}};
    QVERIFY(ExtensionStorage::setValue(id, QStringLiteral("obj"), object).isWritten);
    QCOMPARE(ExtensionStorage::value(id, QStringLiteral("obj")).toObject(), object);
    QVERIFY(ExtensionStorage::value(id, QStringLiteral("missing")).isNull());
}

void TestExtensionBridge::storageIsPerExtension()
{
    QVERIFY(ExtensionStorage::setValue(QStringLiteral("sample"), QStringLiteral("k"), QJsonValue(1)).isWritten);
    QVERIFY(ExtensionStorage::value(QStringLiteral("other"), QStringLiteral("k")).isNull());
    QCOMPARE(ExtensionStorage::keys(QStringLiteral("sample")), QStringList{QStringLiteral("k")});
    QVERIFY(ExtensionStorage::keys(QStringLiteral("other")).isEmpty());
}

void TestExtensionBridge::bridgeRejectsWrongToken()
{
    allowInPrivateWindows(QStringLiteral("sample"));
    const QString good = sampleToken();
    QVERIFY(!good.isEmpty());
    QVERIFY(m_fixture.client().isOk(QStringLiteral("storage.keys")));

    const BridgeClient wrongToken{m_fixture.bridge.get(), QStringLiteral("sample"), QStringLiteral("wrong")};
    QVERIFY(!wrongToken.isOk(QStringLiteral("storage.keys")));
    QCOMPARE(errorOf(wrongToken.call(QStringLiteral("storage.keys"))), QStringLiteral("Invalid extension token"));
    QVERIFY(!BridgeClient({m_fixture.bridge.get(), QStringLiteral("sample"), QString()}).isOk(QStringLiteral("storage.keys")));
    QVERIFY(!BridgeClient({m_fixture.bridge.get(), QStringLiteral("other"), good}).isOk(QStringLiteral("storage.keys")));
    ExtensionBridge orphan;
    QVERIFY(!BridgeClient({&orphan, QStringLiteral("sample"), good}).isOk(QStringLiteral("storage.keys")));
}

void TestExtensionBridge::bridgeRefusesDownloadWithoutPermission()
{
    allowInPrivateWindows(QStringLiteral("sample"));
    const QJsonObject download = m_fixture.client().call(QStringLiteral("download"),
                                               {QStringLiteral("https://example.com/f.zip"), QString()});
    QVERIFY(!download.value(QStringLiteral("ok")).toBool());
    QVERIFY(errorOf(download).contains(QLatin1String("\"downloads\"")));
}

void TestExtensionBridge::installSampleWithoutTabsPermission()
{
    const QString zip = packVariant(m_work.path(), QStringLiteral("notabs"), [](QJsonObject &manifest) {
        manifest.insert(QStringLiteral("permissions"), QJsonArray());
    });
    QVERIFY(!zip.isEmpty());
    const InstallResult installed = ExtensionManager::instance()->installPackage({zip, QStringLiteral("file")}, QStringLiteral("sample"));
    QVERIFY2(installed.isInstalled, qPrintable(installed.error));
    allowInPrivateWindows(QStringLiteral("sample"));
}

void TestExtensionBridge::bridgeRefusesTabsWithoutPermission()
{
    const QString good = sampleToken();
    allowInPrivateWindows(QStringLiteral("sample"));
    installSampleWithoutTabsPermission();
    const BridgeClient withoutTabs = m_fixture.client();
    QVERIFY(withoutTabs.token != good);
    QSignalSpy closes(m_fixture.tab.get(), &Tab::closeRequested);
    const QJsonObject close = withoutTabs.call(QStringLiteral("tabs.close"));
    QVERIFY(!close.value(QStringLiteral("ok")).toBool());
    QVERIFY(errorOf(close).contains(QLatin1String("\"tabs\"")));
    QCOMPARE(closes.count(), 0);
    QVERIFY(!withoutTabs.isOk(QStringLiteral("notify"), {QStringLiteral("t"), QStringLiteral("b")}));
}

void TestExtensionBridge::bridgeOffExtension()
{
    const BridgeClient good = m_fixture.client();
    allowInPrivateWindows(QStringLiteral("sample"));
    ExtensionManager::instance()->setEnabled(QStringLiteral("sample"), false);
    QVERIFY(!good.isOk(QStringLiteral("storage.keys")));
}

int runTestExtensionBridge(int argc, char *argv[])
{
    TestExtensionBridge test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensionbridge.moc"
