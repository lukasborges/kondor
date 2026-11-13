#include "catalogharness.h"

class TestExtensionCatalog : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanup();
    void silentUpdateRule();
    void catalogListsEntries();
    void catalogInstallAsksForConfirmation();
    void catalogRejectsBadChecksum();
    void catalogRejectsOversizedPackage();

private:
    CatalogFixture fixture(const QString &version = QStringLiteral("1.0.0")) const;

    QTemporaryDir m_root;
};

void TestExtensionCatalog::initTestCase()
{
    QVERIFY(m_root.isValid());
}

void TestExtensionCatalog::cleanup()
{
    removeEveryExtension();
}

CatalogFixture TestExtensionCatalog::fixture(const QString &version) const
{
    return catalogFixture(m_root.path(), version, {QStringLiteral("tabs")});
}

void TestExtensionCatalog::silentUpdateRule()
{
    const QStringList matches{QStringLiteral("https://a.com/*"), QStringLiteral("https://b.com/*")};
    const QStringList permissions{QStringLiteral("tabs")};
    using C = ExtensionCatalog;
    QVERIFY(C::isSilentUpdate({matches, permissions}, {matches, permissions}));
    QVERIFY(C::isSilentUpdate({{QStringLiteral("https://a.com/*")}, {}}, {matches, permissions}));
    QVERIFY(C::isSilentUpdate({{}, {}}, {matches, permissions}));
    QVERIFY(!C::isSilentUpdate({{QStringLiteral("https://c.com/*")}, permissions}, {matches, permissions}));
    QVERIFY(!C::isSilentUpdate({matches, {QStringLiteral("tabs"), QStringLiteral("downloads")}}, {matches, permissions}));
    QVERIFY(!C::isSilentUpdate({{QStringLiteral("<all_urls>")}, permissions}, {matches, permissions}));
}

void TestExtensionCatalog::catalogListsEntries()
{
    verifyRefreshed(writeCatalog(fixture()));
    ExtensionCatalog *catalog = ExtensionCatalog::instance();
    QCOMPARE(catalog->rowCount(), 1);
    const QModelIndex row = catalog->index(0);
    QCOMPARE(catalog->data(row, ExtensionCatalog::IdRole).toString(), QStringLiteral("sample"));
    QCOMPARE(catalog->data(row, ExtensionCatalog::NameRole).toString().isEmpty(), false);
    QCOMPARE(catalog->data(row, ExtensionCatalog::IconSourceRole).toString(), QStringLiteral("weather-clear-night"));
    QVERIFY(!catalog->data(row, ExtensionCatalog::InstalledRole).toBool());
    QVERIFY(QFileInfo(ExtensionCatalog::cacheFile()).isFile());
}

void TestExtensionCatalog::catalogInstallAsksForConfirmation()
{
    verifyRefreshed(writeCatalog(fixture()));
    ExtensionCatalog *catalog = ExtensionCatalog::instance();
    catalog->install(QStringLiteral("sample"));
    ExtensionManager *manager = ExtensionManager::instance();
    verifyPendingInstallAppears();
    QVERIFY(manager->pendingInstall().value(QStringLiteral("valid")).toBool());
    QVERIFY(!manager->pendingInstall().value(QStringLiteral("fromFile")).toBool());
    QVERIFY(!manager->isInstalled(QStringLiteral("sample")));
    manager->confirmInstall();
    QVERIFY(manager->isInstalled(QStringLiteral("sample")));
    QCOMPARE(manager->source(QStringLiteral("sample")), QStringLiteral("catalog"));
    QVERIFY(catalog->data(catalog->index(0), ExtensionCatalog::InstalledRole).toBool());
    QVERIFY(catalog->installError().isEmpty());
}

void TestExtensionCatalog::catalogRejectsBadChecksum()
{
    CatalogFixture broken = fixture();
    broken.checksum = QString(64, QLatin1Char('0'));
    ExtensionCatalog *catalog = ExtensionCatalog::instance();
    verifyRefreshed(writeCatalog(broken));
    catalog->install(QStringLiteral("sample"));
    QVERIFY(QTest::qWaitFor([&]() { return !catalog->installError().isEmpty(); }, 10000));
    QVERIFY2(catalog->installError().contains(QLatin1String("checksum")), qPrintable(catalog->installError()));
    QVERIFY(ExtensionManager::instance()->pendingInstall().isEmpty());
    QVERIFY(!ExtensionManager::instance()->isInstalled(QStringLiteral("sample")));
    QVERIFY(catalog->installingId().isEmpty());
}

void TestExtensionCatalog::catalogRejectsOversizedPackage()
{
    CatalogFixture oversized = fixture();
    oversized.size = 10;
    ExtensionCatalog *catalog = ExtensionCatalog::instance();
    verifyRefreshed(writeCatalog(oversized));
    catalog->install(QStringLiteral("sample"));
    QVERIFY(QTest::qWaitFor([&]() { return !catalog->installError().isEmpty(); }, 10000));
    QVERIFY(ExtensionManager::instance()->pendingInstall().isEmpty());
    QVERIFY(!ExtensionManager::instance()->isInstalled(QStringLiteral("sample")));
}

int runTestExtensionCatalog(int argc, char *argv[])
{
    TestExtensionCatalog test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensioncatalog.moc"
