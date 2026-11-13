#include "../extensionsharness.h"

class TestExtensionInstall : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanup();
    void inspectFileShowsPreview();
    void confirmInstallInstallsTheExtension();
    void reloadFindsTheInstall();
    void inspectAgainOffersReplacing();
    void notAZipShowsError();
    void zipWithoutManifestShowsError();

private:
    void inspectAndConfirmSample();

    QTemporaryDir m_work;
};

void TestExtensionInstall::initTestCase()
{
    QVERIFY(m_work.isValid());
}

void TestExtensionInstall::cleanup()
{
    removeEveryExtension();
}

void TestExtensionInstall::inspectAndConfirmSample()
{
    ExtensionManager *manager = ExtensionManager::instance();
    manager->inspectFile(samplePackage(m_work.path()));
    manager->confirmInstall();
}

void TestExtensionInstall::inspectFileShowsPreview()
{
    ExtensionManager *manager = ExtensionManager::instance();
    QSignalSpy pending(manager, &ExtensionManager::pendingInstallChanged);

    manager->inspectFile(samplePackage(m_work.path()));
    QCOMPARE(pending.count(), 1);
    const QVariantMap preview = manager->pendingInstall();
    QVERIFY(preview.value(QStringLiteral("valid")).toBool());
    QVERIFY(preview.value(QStringLiteral("fromFile")).toBool());
    QCOMPARE(preview.value(QStringLiteral("name")).toString(), QStringLiteral("Sample Extension"));
    QCOMPARE(preview.value(QStringLiteral("installedVersion")).toString(), QString());
    const QVariantList entries = preview.value(QStringLiteral("permissions")).toList();
    QCOMPARE(entries.size(), 3);
    QCOMPARE(entries.first().toMap().value(QStringLiteral("text")).toString(),
             QStringLiteral("Read and change pages on 127.0.0.1, localhost"));
    QVERIFY(!manager->isInstalled(QStringLiteral("sample")));
}

void TestExtensionInstall::confirmInstallInstallsTheExtension()
{
    ExtensionManager *manager = ExtensionManager::instance();
    inspectAndConfirmSample();
    QVERIFY(manager->pendingInstall().isEmpty());
    QVERIFY(manager->isInstalled(QStringLiteral("sample")));
    QCOMPARE(manager->source(QStringLiteral("sample")), QStringLiteral("file"));
    QCOMPARE(ExtensionManager::instance()->count(), 1);
    QVERIFY(QFileInfo(ExtensionManager::extensionsDirectory() + QStringLiteral("/sample/manifest.json")).isFile());
    const QModelIndex row = manager->index(0);
    QCOMPARE(manager->data(row, ExtensionManager::NameRole).toString(), QStringLiteral("Sample Extension"));
    QVERIFY(manager->data(row, ExtensionManager::EnabledRole).toBool());
    QVERIFY(!manager->data(row, ExtensionManager::PrivateAllowedRole).toBool());
    QVERIFY(manager->data(row, ExtensionManager::HasSettingsRole).toBool());
    QVERIFY(manager->data(row, ExtensionManager::HasActionRole).toBool());
}

void TestExtensionInstall::reloadFindsTheInstall()
{
    inspectAndConfirmSample();
    ExtensionManager::instance()->reload();
    QCOMPARE(ExtensionManager::instance()->count(), 1);
}

void TestExtensionInstall::inspectAgainOffersReplacing()
{
    inspectAndConfirmSample();
    ExtensionManager *manager = ExtensionManager::instance();
    manager->inspectFile(samplePackage(m_work.path()));
    QCOMPARE(manager->pendingInstall().value(QStringLiteral("installedVersion")).toString(),
             QStringLiteral("1.0.0"));
    manager->cancelInstall();
    QVERIFY(manager->pendingInstall().isEmpty());
}

void TestExtensionInstall::notAZipShowsError()
{
    ExtensionManager *manager = ExtensionManager::instance();
    const QString notZip = m_work.path() + QStringLiteral("/not-a-zip.kondorext");
    QVERIFY(writeFile(notZip, "this is not a zip"));
    manager->inspectFile(notZip);
    QVERIFY(!manager->pendingInstall().value(QStringLiteral("valid")).toBool());
    QVERIFY(!manager->pendingInstall().value(QStringLiteral("error")).toString().isEmpty());
    QCOMPARE(manager->pendingInstall().value(QStringLiteral("fileName")).toString(),
             QStringLiteral("not-a-zip.kondorext"));
}

void TestExtensionInstall::zipWithoutManifestShowsError()
{
    ExtensionManager *manager = ExtensionManager::instance();
    const QString noManifest = m_work.path() + QStringLiteral("/no-manifest.kondorext");
    {
        KZip zip(noManifest);
        QVERIFY(zip.open(QIODevice::WriteOnly));
        QVERIFY(zip.writeFile(QStringLiteral("content.js"), QByteArray("x")));
        QVERIFY(zip.close());
    }
    manager->inspectFile(noManifest);
    QCOMPARE(manager->pendingInstall().value(QStringLiteral("error")).toString(),
             QStringLiteral("manifest.json: file not found"));
    QCOMPARE(manager->count(), 0);
    const QStringList leftovers = QDir(ExtensionManager::extensionsDirectory())
                                      .entryList(QDir::Dirs | QDir::NoDotAndDotDot | QDir::Hidden);
    QVERIFY2(leftovers.isEmpty() || (leftovers.size() == 0), qPrintable(leftovers.join(QLatin1Char(','))));
}

int runTestExtensionInstall(int argc, char *argv[])
{
    TestExtensionInstall test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensioninstall.moc"
