#include "extensionsharness.h"

class TestExtensionScripts : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanup();
    void scriptMetadata();
    void scriptsForNormalProfile();
    void runAtMapping_data();
    void runAtMapping();
    void privateProfileScripts();
    void disabledSiteIsInScript();

private:
    QString sampleScript(bool isPrivate);

    QTemporaryDir m_work;
};

void TestExtensionScripts::initTestCase()
{
    QVERIFY(m_work.isValid());
}

void TestExtensionScripts::cleanup()
{
    removeEveryExtension();
}

QString TestExtensionScripts::sampleScript(bool isPrivate)
{
    return ExtensionManager::instance()->scriptSource(QStringLiteral("sample"), 0, isPrivate);
}

void TestExtensionScripts::scriptMetadata()
{
    QVERIFY(installSample(m_work.path()));
    const QString source = sampleScript(false);
    QVERIFY(source.startsWith(QStringLiteral("// ==UserScript==\n")));
    QVERIFY(source.contains(QStringLiteral("// @match *://127.0.0.1/*\n")));
    QVERIFY(source.contains(QStringLiteral("// @match *://localhost/*\n")));
    QVERIFY(source.contains(QStringLiteral("// @exclude *://127.0.0.1:*/excluded/*\n")));
    QVERIFY(source.contains(QStringLiteral("// @run-at document-end\n// ==/UserScript==\n")));
    QVERIFY(source.contains(QStringLiteral("border-top: 4px solid #3daee9")));
    QVERIFY(source.contains(QStringLiteral("data-kondor-sample")));
    QVERIFY(source.contains(QStringLiteral("__kondorCreateRuntime")));
    QVERIFY(!source.contains(QStringLiteral("\"token\":\"\"")));
}

void TestExtensionScripts::scriptsForNormalProfile()
{
    QVERIFY(installSample(m_work.path()));
    const QList<QWebEngineScript> scripts = ExtensionManager::instance()->scriptsFor(false);
    QCOMPARE(scripts.size(), 1);
    QCOMPARE(scripts.first().name(), QStringLiteral("kondor-ext:sample:0"));
    QCOMPARE(scripts.first().worldId(), uint(QWebEngineScript::ApplicationWorld));
    QVERIFY(!scripts.first().runsOnSubFrames());
}

void TestExtensionScripts::runAtMapping_data()
{
    QTest::addColumn<QString>("runAt");
    QTest::addColumn<int>("point");
    QTest::newRow("start") << QStringLiteral("document-start") << int(QWebEngineScript::DocumentCreation);
    QTest::newRow("end") << QStringLiteral("document-end") << int(QWebEngineScript::DocumentReady);
    QTest::newRow("idle") << QStringLiteral("document-idle") << int(QWebEngineScript::Deferred);
}

void TestExtensionScripts::runAtMapping()
{
    QFETCH(QString, runAt);
    QFETCH(int, point);
    const QString zip = packVariant(m_work.path(), QStringLiteral("runat"), [&](QJsonObject &manifest) {
        QJsonArray scripts = manifest.value(QLatin1String("contentScripts")).toArray();
        QJsonObject script = scripts.first().toObject();
        script.insert(QStringLiteral("runAt"), runAt);
        script.insert(QStringLiteral("allFrames"), true);
        scripts[0] = script;
        manifest.insert(QStringLiteral("contentScripts"), scripts);
    });
    QVERIFY(!zip.isEmpty());
    ExtensionManager *manager = ExtensionManager::instance();
    const InstallResult installed = manager->installPackage({zip, QStringLiteral("file")}, QStringLiteral("sample"));
    QVERIFY2(installed.isInstalled, qPrintable(installed.error));
    const QList<QWebEngineScript> scripts = manager->scriptsFor(false);
    QCOMPARE(scripts.size(), 1);
    QCOMPARE(int(scripts.first().injectionPoint()), point);
    QVERIFY(scripts.first().runsOnSubFrames());
    QVERIFY(scripts.first().sourceCode().contains(QStringLiteral("// @run-at %1\n").arg(runAt)));
}

void TestExtensionScripts::privateProfileScripts()
{
    QVERIFY(installSample(m_work.path()));
    ExtensionManager *manager = ExtensionManager::instance();
    QCOMPARE(manager->scriptsFor(true).size(), 0);
    QCOMPARE(manager->scriptsFor(false).size(), 1);

    allowInPrivateWindows(QStringLiteral("sample"));
    QCOMPARE(manager->scriptsFor(true).size(), 1);
    QVERIFY(sampleScript(true).contains(QStringLiteral("\"isPrivate\":true")));

    manager->setEnabled(QStringLiteral("sample"), false);
    QCOMPARE(manager->scriptsFor(false).size(), 0);
    QCOMPARE(manager->scriptsFor(true).size(), 0);
}

void TestExtensionScripts::disabledSiteIsInScript()
{
    QVERIFY(installSample(m_work.path()));
    ExtensionManager *manager = ExtensionManager::instance();
    const QUrl url(QStringLiteral("https://example.com/page?q=1"));
    QVERIFY(manager->siteEnabled(QStringLiteral("sample"), url));
    manager->setSiteEnabled(QStringLiteral("sample"), url, false);
    QVERIFY(!manager->siteEnabled(QStringLiteral("sample"), url));
    QVERIFY(manager->siteEnabled(QStringLiteral("sample"), QUrl(QStringLiteral("https://other.example/"))));
    QVERIFY(sampleScript(false).contains(QStringLiteral("\"disabledSites\":[\"https://example.com\"]")));
    QCOMPARE(manager->configurationFor(QStringLiteral("sample")).value(QStringLiteral("disabledSites")).toStringList(),
             QStringList{QStringLiteral("https://example.com")});
    manager->setSiteEnabled(QStringLiteral("sample"), url, true);
    QVERIFY(manager->siteEnabled(QStringLiteral("sample"), url));
    QCOMPARE(ExtensionManager::originOf(QUrl(QStringLiteral("file:///tmp/a.html"))), QString());
    QCOMPARE(ExtensionManager::originOf(QUrl(QStringLiteral("https://Example.com:8443/x"))),
             QStringLiteral("https://example.com:8443"));
}

int runTestExtensionScripts(int argc, char *argv[])
{
    TestExtensionScripts test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensionscripts.moc"
