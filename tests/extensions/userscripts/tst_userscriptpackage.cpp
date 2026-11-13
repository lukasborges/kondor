#include "../extensionsharness.h"
#include "extensions/userscripts/userscriptpackage.h"

class TestUserScriptPackage : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanup();
    void idIsStableForNameAndNamespace();
    void manifestLoadsBackWithIncludeAndUserScript();
    void includeGlobsDescribeSiteAccess_data();
    void includeGlobsDescribeSiteAccess();
    void installsFileWithRequirement();
    void refusesInvalidFile();
    void identicalScriptOffersReplace();

private:
    QString copyFixture(const QString &name);

    QTemporaryDir m_work;
};

namespace {

QString idOfFixture(const QString &path)
{
    QFile file(path);
    QString error;
    if (!file.open(QIODevice::ReadOnly))
        return QString();
    const auto metadata = parseUserScriptMetadata(QString::fromUtf8(file.readAll()), error);
    return metadata ? userScriptId(*metadata) : QString();
}

QVariantMap pending()
{
    return ExtensionManager::instance()->pendingInstall();
}

}

void TestUserScriptPackage::initTestCase()
{
    QVERIFY(m_work.isValid());
}

void TestUserScriptPackage::cleanup()
{
    removeEveryExtension();
}

QString TestUserScriptPackage::copyFixture(const QString &name)
{
    const QString directory = m_work.path() + QLatin1Char('/');
    for (const QString &file : {name, QStringLiteral("lib.js")}) {
        QFile::remove(directory + file);
        QFile::copy(QStringLiteral(KONDOR_TEST_DATA_DIR "/userscripts/") + file, directory + file);
    }
    return directory + name;
}

void TestUserScriptPackage::idIsStableForNameAndNamespace()
{
    const QString id = idOfFixture(copyFixture(QStringLiteral("wide.user.js")));
    QVERIFY(ExtensionPackage::isValidId(id));
    QVERIFY(id.startsWith(QLatin1String("user-")));
    UserScriptMetadata other;
    other.name = QStringLiteral("Wide Test");
    other.namespaceName = QStringLiteral("test");
    QCOMPARE(userScriptId(other), id);
    other.namespaceName = QStringLiteral("elsewhere");
    QVERIFY(userScriptId(other) != id);
}

void TestUserScriptPackage::manifestLoadsBackWithIncludeAndUserScript()
{
    QVERIFY(ExtensionManager::instance()->count() == 0);
    ExtensionManager *manager = ExtensionManager::instance();
    manager->inspectUserScript(QUrl::fromLocalFile(copyFixture(QStringLiteral("wide.user.js"))));
    QTRY_VERIFY2(pending().value(QStringLiteral("valid")).toBool(), qPrintable(pending().value(QStringLiteral("error")).toString()));
    manager->confirmInstall();
    const QString id = idOfFixture(copyFixture(QStringLiteral("wide.user.js")));
    const ExtensionPackage package = ExtensionPackage::load(
        ExtensionManager::extensionsDirectory() + QLatin1Char('/') + id);
    QVERIFY(package.isValid());
    QCOMPARE(package.version(), QStringLiteral("1.0.0"));
    QCOMPARE(package.allIncludes(), QStringList{QStringLiteral("https://*.example.org/*")});
    QCOMPARE(package.userScript().value(QLatin1String("version")).toString(), QStringLiteral("1.0"));
    QVERIFY(package.hasPermission(QStringLiteral("notifications")));
    QVERIFY(!package.contentScripts().first().allFrames);
    QVERIFY(!package.readFile(QStringLiteral("require-1.js")).isEmpty());
}

void TestUserScriptPackage::includeGlobsDescribeSiteAccess_data()
{
    QTest::addColumn<QString>("glob");
    QTest::addColumn<QString>("expected");
    QTest::newRow("wildcard host") << "https://*.example.org/*" << "Read and change all websites";
    QTest::newRow("empty host") << "file:///*" << "Read and change all websites";
    QTest::newRow("no scheme") << "example.org*" << "Read and change all websites";
    QTest::newRow("plain host") << "https://example.org/*" << "Read and change pages on example.org";
}

void TestUserScriptPackage::includeGlobsDescribeSiteAccess()
{
    QFETCH(QString, glob);
    QFETCH(QString, expected);
    const QStringList lines = ExtensionPackage::permissionLines({}, {}, {glob});
    QCOMPARE(lines, QStringList{expected});
}

void TestUserScriptPackage::installsFileWithRequirement()
{
    ExtensionManager *manager = ExtensionManager::instance();
    QSignalSpy manage(manager, &ExtensionManager::manageRequested);
    manager->inspectFile(QUrl::fromLocalFile(copyFixture(QStringLiteral("wide.user.js"))).toString());
    QCOMPARE(manage.count(), 1);
    QTRY_VERIFY2(pending().value(QStringLiteral("valid")).toBool(), qPrintable(pending().value(QStringLiteral("error")).toString()));
    QVERIFY(pending().value(QStringLiteral("isUserScript")).toBool());
    QCOMPARE(pending().value(QStringLiteral("unsupportedFeatures")).toStringList(),
             (QStringList{QStringLiteral("GM_xmlhttpRequest"), QStringLiteral("@resource")}));
    QVERIFY(pending().value(QStringLiteral("permissions")).toList().size() == 2);
    manager->confirmInstall();
    const QString id = idOfFixture(copyFixture(QStringLiteral("wide.user.js")));
    QVERIFY(manager->isInstalled(id));
    QCOMPARE(manager->source(id), QStringLiteral("userscript"));
    QCOMPARE(manager->installedVersion(id), QStringLiteral("1.0.0"));
}

void TestUserScriptPackage::refusesInvalidFile()
{
    ExtensionManager *manager = ExtensionManager::instance();
    manager->inspectFile(copyFixture(QStringLiteral("no-name.user.js")));
    QTRY_VERIFY(pending().value(QStringLiteral("valid")).isValid());
    QVERIFY(!pending().value(QStringLiteral("valid")).toBool());
    QVERIFY(pending().value(QStringLiteral("isUserScript")).toBool());
    QVERIFY(!pending().value(QStringLiteral("error")).toString().isEmpty());
    manager->cancelInstall();
}

void TestUserScriptPackage::identicalScriptOffersReplace()
{
    ExtensionManager *manager = ExtensionManager::instance();
    const QUrl url = QUrl::fromLocalFile(copyFixture(QStringLiteral("wide.user.js")));
    manager->inspectUserScript(url);
    QTRY_VERIFY2(pending().value(QStringLiteral("valid")).toBool(), qPrintable(pending().value(QStringLiteral("error")).toString()));
    manager->confirmInstall();
    manager->inspectUserScript(url);
    QTRY_COMPARE(pending().value(QStringLiteral("installedVersion")).toString(), QStringLiteral("1.0.0"));
    manager->cancelInstall();
}

int runTestUserScriptPackage(int argc, char *argv[])
{
    TestUserScriptPackage test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_userscriptpackage.moc"
