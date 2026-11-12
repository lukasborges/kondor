#include "catalogharness.h"

class TestExtensionUpdates : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void init();
    void cleanup();
    void newerVersionWithoutNewPermissionsInstallsItself();
    void newPermissionOnlyMarksUpdateForReview();
    void catalogClaimingOldPermissionsIsNotSilent();
    void updateAsksFirstWithReplacementText();
    void nothingUpdatesWhenAutomaticUpdatesAreOff();
    void fileInstallsAreNeverUpdatedAutomatically();

private:
    CatalogFixture fixture(const QString &version, const QStringList &permissions) const;

    QTemporaryDir m_work;
    QTemporaryDir m_root;
};

void TestExtensionUpdates::initTestCase()
{
    QVERIFY(m_work.isValid());
    QVERIFY(m_root.isValid());
}

void TestExtensionUpdates::init()
{
    Settings::instance()->setExtensionsAutoUpdate(true);
}

void TestExtensionUpdates::cleanup()
{
    removeEveryExtension();
}

CatalogFixture TestExtensionUpdates::fixture(const QString &version, const QStringList &permissions) const
{
    return catalogFixture(m_root.path(), version, permissions);
}

void TestExtensionUpdates::newerVersionWithoutNewPermissionsInstallsItself()
{
    ExtensionManager *manager = ExtensionManager::instance();
    verifyInstalledFromCatalog(fixture(QStringLiteral("1.0.0"), {QStringLiteral("tabs")}));
    verifyRefreshed(writeCatalog(fixture(QStringLiteral("1.1.0"), {QStringLiteral("tabs")})));
    QVERIFY(QTest::qWaitFor([&]() { return installedSampleVersion() == QLatin1String("1.1.0"); }, 10000));
    QVERIFY(manager->pendingInstall().isEmpty());
    QVERIFY(!manager->data(manager->index(0), ExtensionManager::UpdateAvailableRole).toBool());
}

void TestExtensionUpdates::newPermissionOnlyMarksUpdateForReview()
{
    const QStringList withDownloads{QStringLiteral("tabs"), QStringLiteral("downloads")};
    verifyInstalledFromCatalog(fixture(QStringLiteral("1.1.0"), {QStringLiteral("tabs")}));
    verifyRefreshed(writeCatalog(fixture(QStringLiteral("1.2.0"), withDownloads)));
    QVERIFY(QTest::qWaitFor([]() { return isUpdateWaitingForReview(); }, 10000));
    QCOMPARE(installedSampleVersion(), QStringLiteral("1.1.0"));
    ExtensionCatalog *catalog = ExtensionCatalog::instance();
    QVERIFY(catalog->data(catalog->index(0), ExtensionCatalog::UpdateAvailableRole).toBool());
}

void TestExtensionUpdates::catalogClaimingOldPermissionsIsNotSilent()
{
    verifyInstalledFromCatalog(fixture(QStringLiteral("1.1.0"), {QStringLiteral("tabs")}));
    CatalogFixture claiming = fixture(QStringLiteral("1.1.5"), {QStringLiteral("tabs"), QStringLiteral("downloads")});
    claiming.catalogPermissions = QStringList{QStringLiteral("tabs")};
    verifyRefreshed(writeCatalog(claiming));
    QVERIFY(QTest::qWaitFor([]() { return isUpdateWaitingForReview(); }, 10000));
    QCOMPARE(installedSampleVersion(), QStringLiteral("1.1.0"));
    const ExtensionAccess access = ExtensionManager::instance()->installedAccess(QStringLiteral("sample"));
    QVERIFY(!access.permissions.contains(QLatin1String("downloads")));
}

void TestExtensionUpdates::updateAsksFirstWithReplacementText()
{
    ExtensionManager *manager = ExtensionManager::instance();
    verifyInstalledFromCatalog(fixture(QStringLiteral("1.1.0"), {QStringLiteral("tabs")}));
    verifyRefreshed(writeCatalog(fixture(QStringLiteral("1.2.0"), {QStringLiteral("tabs"), QStringLiteral("downloads")})));
    QTest::qWait(300);
    QCOMPARE(installedSampleVersion(), QStringLiteral("1.1.0"));

    ExtensionCatalog::instance()->install(QStringLiteral("sample"));
    verifyPendingInstallAppears();
    QCOMPARE(manager->pendingInstall().value(QStringLiteral("installedVersion")).toString(), QStringLiteral("1.1.0"));
    QCOMPARE(manager->pendingInstall().value(QStringLiteral("version")).toString(), QStringLiteral("1.2.0"));
    manager->confirmInstall();
    QCOMPARE(installedSampleVersion(), QStringLiteral("1.2.0"));
}

void TestExtensionUpdates::nothingUpdatesWhenAutomaticUpdatesAreOff()
{
    const QStringList withDownloads{QStringLiteral("tabs"), QStringLiteral("downloads")};
    verifyInstalledFromCatalog(fixture(QStringLiteral("1.2.0"), withDownloads));
    Settings::instance()->setExtensionsAutoUpdate(false);
    verifyRefreshed(writeCatalog(fixture(QStringLiteral("1.3.0"), withDownloads)));
    QTest::qWait(300);
    QCOMPARE(installedSampleVersion(), QStringLiteral("1.2.0"));
}

void TestExtensionUpdates::fileInstallsAreNeverUpdatedAutomatically()
{
    QVERIFY(installSample(m_work.path(), QStringLiteral("file")));
    QCOMPARE(installedSampleVersion(), QStringLiteral("1.0.0"));
    verifyRefreshed(writeCatalog(fixture(QStringLiteral("1.3.0"), {QStringLiteral("tabs"), QStringLiteral("downloads")})));
    QTest::qWait(300);
    QCOMPARE(installedSampleVersion(), QStringLiteral("1.0.0"));
}

int runTestExtensionUpdates(int argc, char *argv[])
{
    TestExtensionUpdates test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensionupdates.moc"
