#include <memory>

#include "browser/profilemanager.h"
#include "extensionpageharness.h"
#include "pageserver.h"

class TestExtensionPages : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void init();
    void cleanup();
    void runsInNormalPagesWithSettingsAndStorage();
    void settingChangeReachesTheOpenPage();
    void toolbarActionReachesTheExtension();
    void excludedPathDoesNotRunIt();
    void privatePagesNeedPermissionAndGetReadOnlyStorage();
    void disabledSiteDoesNotRunIt();

private:
    Page openNormal(const QString &path = QStringLiteral("/"));
    Page openPrivate(const QString &path = QStringLiteral("/"));
    void verifyScriptRan(const Page &page, const QString &greeting);

    QTemporaryDir m_work;
    PageServer m_server;
    QQuickWebEngineProfile *m_normalProfile = nullptr;
    QQuickWebEngineProfile *m_privateProfile = nullptr;
    std::unique_ptr<PageHost> m_host;
};

void TestExtensionPages::initTestCase()
{
    QVERIFY(m_work.isValid());
    QVERIFY(m_server.port() > 0);
    m_server.start();
    ProfileManager *profiles = ProfileManager::instance();
    QObject::connect(profiles, &ProfileManager::profileCreated,
                     ExtensionManager::instance(), &ExtensionManager::registerProfile);
    m_normalProfile = profiles->defaultProfile();
    ExtensionManager::instance()->registerProfile(m_normalProfile);
}

void TestExtensionPages::init()
{
    m_privateProfile = ProfileManager::instance()->createPrivateProfile();
    QVERIFY(installSample(m_work.path()));
    m_host.reset(new PageHost);
}

void TestExtensionPages::cleanup()
{
    m_host.reset();
    removeEveryExtension();
}

Page TestExtensionPages::openNormal(const QString &path)
{
    return m_host->open(m_normalProfile, m_server.url(path));
}

Page TestExtensionPages::openPrivate(const QString &path)
{
    return m_host->open(m_privateProfile, m_server.url(path));
}

void TestExtensionPages::verifyScriptRan(const Page &page, const QString &greeting)
{
    QTRY_COMPARE_WITH_TIMEOUT(attribute(page, QStringLiteral("data-kondor-sample")).toString(), greeting, 10000);
}

void TestExtensionPages::runsInNormalPagesWithSettingsAndStorage()
{
    Page normal = openNormal();
    QVERIFY(normal.view);
    QVERIFY(waitLoaded(normal));
    verifyScriptRan(normal, QStringLiteral("hello"));
    QCOMPARE(attribute(normal, QStringLiteral("data-kondor-private")).toString(), QStringLiteral("false"));
    QTRY_COMPARE_WITH_TIMEOUT(attribute(normal, QStringLiteral("data-kondor-storage")).toString(),
                              QStringLiteral("ok"), 10000);
    QCOMPARE(ExtensionStorage::value(QStringLiteral("sample"), QStringLiteral("lastGreeting")).toString(),
             QStringLiteral("hello"));
}

void TestExtensionPages::settingChangeReachesTheOpenPage()
{
    Page normal = openNormal();
    QVERIFY(normal.view);
    QVERIFY(waitLoaded(normal));
    verifyScriptRan(normal, QStringLiteral("hello"));
    applySettings(QStringLiteral("sample"), {{QStringLiteral("greeting"), QStringLiteral("hola")}});
    const QJsonObject values = QJsonObject::fromVariantMap(
        ExtensionManager::instance()->settingValues(QStringLiteral("sample")));
    runInApplicationWorld(normal, QStringLiteral("window.__kondorExtensions['sample'](%1);")
                                      .arg(QString::fromUtf8(QJsonDocument(values).toJson(QJsonDocument::Compact))));
    verifyScriptRan(normal, QStringLiteral("hola"));
}

void TestExtensionPages::toolbarActionReachesTheExtension()
{
    Page normal = openNormal();
    QVERIFY(normal.view);
    QVERIFY(waitLoaded(normal));
    verifyScriptRan(normal, QStringLiteral("hello"));
    runInApplicationWorld(normal, QStringLiteral("window.__kondorExtensionActions['sample']('toggle', true);"));
    QTRY_COMPARE_WITH_TIMEOUT(attribute(normal, QStringLiteral("data-kondor-action")).toString(),
                              QStringLiteral("toggle:true"), 10000);
}

void TestExtensionPages::excludedPathDoesNotRunIt()
{
    Page excluded = openNormal(QStringLiteral("/excluded/page"));
    QVERIFY(excluded.view);
    QVERIFY(waitLoaded(excluded));
    QTest::qWait(500);
    QCOMPARE(attribute(excluded, QStringLiteral("data-kondor-sample")).toString(), QString());
}

void TestExtensionPages::privatePagesNeedPermissionAndGetReadOnlyStorage()
{
    Page priv = openPrivate();
    QVERIFY(priv.view);
    QVERIFY(waitLoaded(priv));
    QTest::qWait(500);
    QCOMPARE(attribute(priv, QStringLiteral("data-kondor-sample")).toString(), QString());

    allowInPrivateWindows(QStringLiteral("sample"));
    QTest::qWait(300);
    loadUrl(priv, m_server.url(QStringLiteral("/again")));
    QVERIFY(waitLoaded(priv));
    QTRY_COMPARE_WITH_TIMEOUT(attribute(priv, QStringLiteral("data-kondor-private")).toString(),
                              QStringLiteral("true"), 10000);
    QTRY_VERIFY_WITH_TIMEOUT(attribute(priv, QStringLiteral("data-kondor-storage")).toString().contains(QLatin1String("read-only")),
                             10000);
}

void TestExtensionPages::disabledSiteDoesNotRunIt()
{
    Page normal = openNormal();
    QVERIFY(normal.view);
    QVERIFY(waitLoaded(normal));
    verifyScriptRan(normal, QStringLiteral("hello"));
    ExtensionManager::instance()->setSiteEnabled(QStringLiteral("sample"), m_server.url(), false);
    QTest::qWait(300);
    loadUrl(normal, m_server.url(QStringLiteral("/after-toggle")));
    QVERIFY(waitLoaded(normal));
    QTest::qWait(500);
    QCOMPARE(evaluate(normal, QStringLiteral("location.pathname")).toString(), QStringLiteral("/after-toggle"));
    QCOMPARE(attribute(normal, QStringLiteral("data-kondor-sample")).toString(), QString());
}

int runTestExtensionPages(int argc, char *argv[])
{
    TestExtensionPages test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensionpages.moc"
