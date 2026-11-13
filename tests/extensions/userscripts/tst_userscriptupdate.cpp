#include "../extensionsharness.h"
#include "scriptserver.h"

namespace {

QVariantMap pending()
{
    return ExtensionManager::instance()->pendingInstall();
}

}

class TestUserScriptUpdate : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanup();
    void silentUpdateKeepsAccess();
    void broaderUpdateNeedsReview();

private:
    QString scriptText(const QString &version, const QString &extraLine);
    void installFromServer();
    void checkForUpdates();

    ScriptServer m_server;
};

void TestUserScriptUpdate::initTestCase()
{
    QVERIFY(m_server.isListening());
}

void TestUserScriptUpdate::cleanup()
{
    removeEveryExtension();
}

QString TestUserScriptUpdate::scriptText(const QString &version, const QString &extraLine)
{
    return QStringLiteral("// ==UserScript==\n// @name Served\n// @namespace test\n// @version %1\n"
                          "// @match *://127.0.0.1/*\n%2\n// @updateURL %3\n// @downloadURL %4\n"
                          "// ==/UserScript==\nvoid 0;\n")
        .arg(version, extraLine, m_server.url(QStringLiteral("/s.meta.js")).toString(),
             m_server.url(QStringLiteral("/s.user.js")).toString());
}

void TestUserScriptUpdate::installFromServer()
{
    m_server.serve(QStringLiteral("/s.user.js"), scriptText(QStringLiteral("1.0"), QString()).toUtf8());
    ExtensionManager::instance()->inspectUserScript(m_server.url(QStringLiteral("/s.user.js")));
    QTRY_VERIFY2(pending().value(QStringLiteral("valid")).toBool(), qPrintable(pending().value(QStringLiteral("error")).toString()));
    ExtensionManager::instance()->confirmInstall();
    Settings::instance()->setExtensionsAutoUpdate(true);
}

void TestUserScriptUpdate::checkForUpdates()
{
    ExtensionCatalog::instance()->checkForUpdates();
}

void TestUserScriptUpdate::silentUpdateKeepsAccess()
{
    installFromServer();
    const QString text = scriptText(QStringLiteral("1.1"), QString());
    m_server.serve(QStringLiteral("/s.meta.js"), text.toUtf8());
    m_server.serve(QStringLiteral("/s.user.js"), text.toUtf8());
    checkForUpdates();
    ExtensionManager *manager = ExtensionManager::instance();
    const QString id = manager->data(manager->index(0), ExtensionManager::IdRole).toString();
    QTRY_COMPARE(manager->installedVersion(id), QStringLiteral("1.1.0"));
}

void TestUserScriptUpdate::broaderUpdateNeedsReview()
{
    installFromServer();
    const QString text = scriptText(QStringLiteral("1.2"), QStringLiteral("// @match *://localhost/*"));
    m_server.serve(QStringLiteral("/s.meta.js"), text.toUtf8());
    m_server.serve(QStringLiteral("/s.user.js"), text.toUtf8());
    checkForUpdates();
    ExtensionManager *manager = ExtensionManager::instance();
    QTRY_VERIFY(manager->data(manager->index(0), ExtensionManager::UpdateNeedsReviewRole).toBool());
    QCOMPARE(manager->installedVersion(manager->data(manager->index(0), ExtensionManager::IdRole).toString()),
             QStringLiteral("1.0.0"));
}

int runTestUserScriptUpdate(int argc, char *argv[])
{
    TestUserScriptUpdate test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_userscriptupdate.moc"
