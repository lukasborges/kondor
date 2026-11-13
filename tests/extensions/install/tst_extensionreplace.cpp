#include <QSettings>

#include "../extensionsharness.h"

class TestExtensionReplace : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanup();
    void replaceKeepsState();
    void packageForAnotherIdIsRefused();
    void removeDeletesEverything();
    void settingsAreSanitized();
    void unchangedSettingsEmitNothing();

private:
    void configureSampleState();
    void replaceSampleWithVersion11();

    QTemporaryDir m_work;
};

void TestExtensionReplace::initTestCase()
{
    QVERIFY(m_work.isValid());
}

void TestExtensionReplace::cleanup()
{
    removeEveryExtension();
}

void TestExtensionReplace::configureSampleState()
{
    const QString id = QStringLiteral("sample");
    ExtensionManager *manager = ExtensionManager::instance();
    manager->applyConfiguration(id, {{QStringLiteral("settings"), QVariantMap{{QStringLiteral("greeting"), QStringLiteral("hi")}}},
                                     {QStringLiteral("privateAllowed"), true},
                                     {QStringLiteral("disabledSites"), QStringList{QStringLiteral("https://example.com")}}});
    manager->setEnabled(id, false);
    QVERIFY(ExtensionStorage::setValue(id, QStringLiteral("k"), QJsonValue(1)).isWritten);
}

void TestExtensionReplace::replaceSampleWithVersion11()
{
    const QString zip = packVariant(m_work.path(), QStringLiteral("v11"), [](QJsonObject &manifest) {
        manifest.insert(QStringLiteral("version"), QStringLiteral("1.1.0"));
    });
    QVERIFY(!zip.isEmpty());
    const InstallResult result = ExtensionManager::instance()->installPackage(
        {zip, QStringLiteral("catalog")}, QStringLiteral("sample"));
    QVERIFY(result.isInstalled);
}

void TestExtensionReplace::replaceKeepsState()
{
    QVERIFY(installSample(m_work.path()));
    configureSampleState();
    replaceSampleWithVersion11();

    const QString id = QStringLiteral("sample");
    ExtensionManager *manager = ExtensionManager::instance();
    QCOMPARE(manager->installedVersion(id), QStringLiteral("1.1.0"));
    QCOMPARE(manager->source(id), QStringLiteral("catalog"));
    QVERIFY(!manager->data(manager->index(0), ExtensionManager::EnabledRole).toBool());
    QVERIFY(manager->data(manager->index(0), ExtensionManager::PrivateAllowedRole).toBool());
    QCOMPARE(manager->settingValues(id).value(QStringLiteral("greeting")).toString(), QStringLiteral("hi"));
    QCOMPARE(ExtensionStorage::value(id, QStringLiteral("k")).toInt(), 1);
    QVERIFY(!QFileInfo::exists(ExtensionManager::extensionsDirectory() + QStringLiteral("/sample.new")));
    QVERIFY(!QFileInfo::exists(ExtensionManager::extensionsDirectory() + QStringLiteral("/sample.old")));
}

void TestExtensionReplace::packageForAnotherIdIsRefused()
{
    QVERIFY(installSample(m_work.path()));
    const QString error = ExtensionManager::instance()->installPackage(
        {samplePackage(m_work.path()), QStringLiteral("catalog")}, QStringLiteral("other")).error;
    QVERIFY(error.contains(QStringLiteral("not “other”")));
}

void TestExtensionReplace::removeDeletesEverything()
{
    QVERIFY(installSample(m_work.path()));
    ExtensionManager *manager = ExtensionManager::instance();
    const QString id = QStringLiteral("sample");
    applySettings(id, {{QStringLiteral("greeting"), QStringLiteral("bye")}});
    QVERIFY(ExtensionStorage::setValue(id, QStringLiteral("k"), QJsonValue(QStringLiteral("v"))).isWritten);

    manager->remove(id);
    QVERIFY(!manager->isInstalled(id));
    QCOMPARE(manager->count(), 0);
    QVERIFY(!QFileInfo::exists(ExtensionManager::extensionsDirectory() + QStringLiteral("/sample")));
    QSettings state(QStringLiteral("KDE"), QStringLiteral("Kondor"));
    state.beginGroup(QStringLiteral("Extensions"));
    QVERIFY(!state.childGroups().contains(id));
    state.endGroup();
    QVERIFY(ExtensionStorage::keys(id).isEmpty());
}

void TestExtensionReplace::settingsAreSanitized()
{
    QVERIFY(installSample(m_work.path()));
    const QString id = QStringLiteral("sample");
    ExtensionManager *manager = ExtensionManager::instance();
    QCOMPARE(manager->settingValues(id).value(QStringLiteral("size")).toInt(), 50);

    applySettings(id, {{QStringLiteral("size"), 500},
                       {QStringLiteral("mode"), QStringLiteral("zzz")},
                       {QStringLiteral("enabledFeature"), QStringLiteral("nope")},
                       {QStringLiteral("greeting"), QStringLiteral("changed")}});
    const QVariantMap values = manager->settingValues(id);
    QCOMPARE(values.value(QStringLiteral("size")).toInt(), 100);
    QCOMPARE(values.value(QStringLiteral("mode")).toString(), QStringLiteral("a"));
    QCOMPARE(values.value(QStringLiteral("enabledFeature")).toBool(), true);
    QCOMPARE(values.value(QStringLiteral("greeting")).toString(), QStringLiteral("changed"));
}

void TestExtensionReplace::unchangedSettingsEmitNothing()
{
    QVERIFY(installSample(m_work.path()));
    const QString id = QStringLiteral("sample");
    applySettings(id, {{QStringLiteral("greeting"), QStringLiteral("changed")}});

    QSignalSpy changed(ExtensionManager::instance(), &ExtensionManager::settingsChanged);
    applySettings(id, {{QStringLiteral("greeting"), QStringLiteral("changed")}});
    QCOMPARE(changed.count(), 0);
    applySettings(id, {{QStringLiteral("greeting"), QStringLiteral("again")}});
    QCOMPARE(changed.count(), 1);
    QCOMPARE(changed.first().first().toString(), id);
}

int runTestExtensionReplace(int argc, char *argv[])
{
    TestExtensionReplace test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensionreplace.moc"
