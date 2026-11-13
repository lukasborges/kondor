#include "../extensionsharness.h"

class TestExtensionPins : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanup();
    void pinnedExtensionsKeepPinOrder();
    void setPinnedIgnoresDuplicates();
    void removeUnpinsExtension();
    void pinnedHidesExtensionsNotAllowedInPrivate();
    void actionExtensionsAreSortedByName();

private:
    static QStringList idsOf(const QVariantList &entries);

    QTemporaryDir m_work;
};

void TestExtensionPins::initTestCase()
{
    QVERIFY(m_work.isValid());
}

void TestExtensionPins::cleanup()
{
    removeEveryExtension();
}

QStringList TestExtensionPins::idsOf(const QVariantList &entries)
{
    QStringList ids;
    for (const QVariant &entry : entries)
        ids.append(entry.toMap().value(QStringLiteral("id")).toString());
    return ids;
}

void TestExtensionPins::pinnedExtensionsKeepPinOrder()
{
    QVERIFY(installNamed(m_work.path(), QStringLiteral("alpha"), QStringLiteral("Alpha")));
    QVERIFY(installNamed(m_work.path(), QStringLiteral("beta"), QStringLiteral("Beta")));
    ExtensionManager *manager = ExtensionManager::instance();
    manager->setPinned(QStringLiteral("beta"), true);
    manager->setPinned(QStringLiteral("alpha"), true);
    QCOMPARE(idsOf(manager->pinnedActionExtensions(false)),
             (QStringList{QStringLiteral("beta"), QStringLiteral("alpha")}));
}

void TestExtensionPins::setPinnedIgnoresDuplicates()
{
    ExtensionManager *manager = ExtensionManager::instance();
    QSignalSpy changes(Settings::instance(), &Settings::pinnedExtensionsChanged);
    manager->setPinned(QStringLiteral("sample"), true);
    manager->setPinned(QStringLiteral("sample"), true);
    QCOMPARE(changes.count(), 1);
    QCOMPARE(Settings::instance()->pinnedExtensions(), QStringList{QStringLiteral("sample")});
}

void TestExtensionPins::removeUnpinsExtension()
{
    QVERIFY(installSample(m_work.path()));
    ExtensionManager *manager = ExtensionManager::instance();
    manager->setPinned(QStringLiteral("sample"), true);
    QVERIFY(manager->isPinned(QStringLiteral("sample")));
    manager->remove(QStringLiteral("sample"));
    QVERIFY(!manager->isPinned(QStringLiteral("sample")));
}

void TestExtensionPins::pinnedHidesExtensionsNotAllowedInPrivate()
{
    QVERIFY(installSample(m_work.path()));
    ExtensionManager *manager = ExtensionManager::instance();
    manager->setPinned(QStringLiteral("sample"), true);
    QCOMPARE(manager->pinnedActionExtensions(true).size(), 0);
    allowInPrivateWindows(QStringLiteral("sample"));
    QCOMPARE(manager->pinnedActionExtensions(true).size(), 1);
}

void TestExtensionPins::actionExtensionsAreSortedByName()
{
    QVERIFY(installNamed(m_work.path(), QStringLiteral("zulu"), QStringLiteral("Zulu")));
    QVERIFY(installNamed(m_work.path(), QStringLiteral("alpha"), QStringLiteral("Alpha")));
    QCOMPARE(idsOf(ExtensionManager::instance()->actionExtensions(false)),
             (QStringList{QStringLiteral("alpha"), QStringLiteral("zulu")}));
}

int runTestExtensionPins(int argc, char *argv[])
{
    TestExtensionPins test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensionpins.moc"
