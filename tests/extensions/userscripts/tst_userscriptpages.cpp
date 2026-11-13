#include <memory>

#include "browser/profile/profilemanager.h"
#include "../bridge/extensionpageharness.h"
#include "../pageserver.h"
#include "extensions/userscripts/userscriptpackage.h"

namespace {

const char kScript[] =
    "// ==UserScript==\n// @name Pages\n// @namespace test\n// @version 1\n"
    "// @match *://127.0.0.1/*\n// @include https://*.example.org/*\n// @grant GM.addStyle\n// @grant GM.setValue\n"
    "// ==/UserScript==\n"
    "GM.addStyle('body { outline: 5px solid red }');\n"
    "document.documentElement.setAttribute('data-us', 'ran');\n"
    "GM.setValue('n', 7).then(() => GM.getValue('n', 0))\n"
    "  .then((n) => document.documentElement.setAttribute('data-n', String(n)));\n";

}

class TestUserScriptPages : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void init();
    void cleanup();
    void runsStylesAndStoresValues();
    void doesNotRunInPrivateProfile();
    void runsWhereMatchOrIncludeAgrees();

private:
    bool installScript();

    QTemporaryDir m_work;
    PageServer m_server;
    QQuickWebEngineProfile *m_normalProfile = nullptr;
    QQuickWebEngineProfile *m_privateProfile = nullptr;
    std::unique_ptr<PageHost> m_host;
};

void TestUserScriptPages::initTestCase()
{
    QVERIFY(m_work.isValid());
    m_server.start();
    ProfileManager *profiles = ProfileManager::instance();
    QObject::connect(profiles, &ProfileManager::profileCreated,
                     ExtensionManager::instance(), &ExtensionManager::registerProfile);
    m_normalProfile = profiles->defaultProfile();
    ExtensionManager::instance()->registerProfile(m_normalProfile);
}

bool TestUserScriptPages::installScript()
{
    UserScriptSource source;
    QString error;
    source.script = kScript;
    source.metadata = parseUserScriptMetadata(QString::fromUtf8(kScript), error).value_or(UserScriptMetadata());
    const auto path = writeUserScriptPackage(source, error);
    if (!path)
        return false;
    const PackageFile file{*path, QStringLiteral("userscript"), QString(), true};
    return ExtensionManager::instance()->installPackage(file, userScriptId(source.metadata)).isInstalled;
}

void TestUserScriptPages::init()
{
    m_privateProfile = ProfileManager::instance()->createPrivateProfile();
    QVERIFY(installScript());
    m_host.reset(new PageHost);
}

void TestUserScriptPages::cleanup()
{
    m_host.reset();
    removeEveryExtension();
}

void TestUserScriptPages::runsStylesAndStoresValues()
{
    Page page = m_host->open(m_normalProfile, m_server.url());
    QVERIFY(page.view);
    QVERIFY(waitLoaded(page));
    QTRY_COMPARE_WITH_TIMEOUT(attribute(page, QStringLiteral("data-us")).toString(), QStringLiteral("ran"), 10000);
    QTRY_COMPARE_WITH_TIMEOUT(attribute(page, QStringLiteral("data-n")).toString(), QStringLiteral("7"), 10000);
    QCOMPARE(evaluate(page, QStringLiteral("getComputedStyle(document.body).outlineStyle")).toString(),
             QStringLiteral("solid"));
}

void TestUserScriptPages::doesNotRunInPrivateProfile()
{
    Page page = m_host->open(m_privateProfile, m_server.url());
    QVERIFY(page.view);
    QVERIFY(waitLoaded(page));
    QTest::qWait(500);
    QCOMPARE(attribute(page, QStringLiteral("data-us")).toString(), QString());
}

void TestUserScriptPages::runsWhereMatchOrIncludeAgrees()
{
    Page page = m_host->open(m_normalProfile, m_server.url());
    QVERIFY(page.view);
    QVERIFY(waitLoaded(page));
    QTRY_COMPARE_WITH_TIMEOUT(attribute(page, QStringLiteral("data-us")).toString(), QStringLiteral("ran"), 10000);
}

int runTestUserScriptPages(int argc, char *argv[])
{
    TestUserScriptPages test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_userscriptpages.moc"
