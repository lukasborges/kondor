#include "settingswindowharness.h"

class TestSettingsApply : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void init();
    void pendingChangesAreDiscarded();
    void applyWritesAndDisablesApply();
    void okAppliesAndCloses();
    void everyPageDefaultsResetOnlyItsOptions_data();
    void everyPageDefaultsResetOnlyItsOptions();
    void walletUnavailableState();

private:
    QQmlEngine m_engine;
};

void TestSettingsApply::initTestCase()
{
    registerSettingsWindowTypes();
}

void TestSettingsApply::init()
{
    resetSettingsToTestDefaults();
}

void TestSettingsApply::pendingChangesAreDiscarded()
{
    SettingsWindowFixture fixture(m_engine);
    QVERIFY(fixture.window());
    fixture.showWindow();
    QVERIFY(fixture.window()->isVisible());
    QObject *pending = fixture.pending();
    QVERIFY(pending);
    QCOMPARE(fixture.isModified(), false);
    pending->setProperty("searchEngine", "google");
    QCOMPARE(fixture.isModified(), true);
    QCOMPARE(Settings::instance()->searchEngine(), QStringLiteral("duckduckgo"));
    fixture.invoke("discardChanges");
    QVERIFY(!fixture.window()->isVisible());
    QCOMPARE(Settings::instance()->searchEngine(), QStringLiteral("duckduckgo"));
    fixture.showWindow();
    QCOMPARE(pending->property("searchEngine").toString(), QStringLiteral("duckduckgo"));
    QCOMPARE(fixture.isModified(), false);
}

void TestSettingsApply::applyWritesAndDisablesApply()
{
    SettingsWindowFixture fixture(m_engine);
    QVERIFY(fixture.window());
    fixture.showWindow();
    QObject *pending = fixture.pending();
    QVERIFY(pending);
    pending->setProperty("searchEngine", "google");
    fixture.invoke("applyChanges");
    QCOMPARE(Settings::instance()->searchEngine(), QStringLiteral("google"));
    QCOMPARE(fixture.isModified(), false);
}

void TestSettingsApply::okAppliesAndCloses()
{
    SettingsWindowFixture fixture(m_engine);
    QVERIFY(fixture.window());
    fixture.showWindow();
    QObject *pending = fixture.pending();
    QVERIFY(pending);
    pending->setProperty("customSearchUrl", "https://example.com/?q=%1");
    fixture.invoke("acceptAndClose");
    QVERIFY(!fixture.window()->isVisible());
    QCOMPARE(Settings::instance()->customSearchUrl(), QStringLiteral("https://example.com/?q=%1"));
}

void TestSettingsApply::everyPageDefaultsResetOnlyItsOptions_data()
{
    QTest::addColumn<int>("page");
    const QStringList titles{ "general", "search", "downloads", "privacy", "passwords",
                              "extensions", "spelling" };
    for (int page = 0; page < titles.size(); ++page)
        QTest::newRow(qPrintable(titles.at(page))) << page;
}

void TestSettingsApply::everyPageDefaultsResetOnlyItsOptions()
{
    QFETCH(int, page);
    SettingsWindowFixture fixture(m_engine);
    QVERIFY(fixture.window());
    fixture.showWindow();
    QObject *draft = fixture.pending();
    QVERIFY(draft);
    for (const auto &option : changedOptionPerPage())
        draft->setProperty(option.first.constData(), option.second);
    fixture.window()->setProperty("currentPage", page);
    QCOMPARE(fixture.window()->property("defaultsEnabled").toBool(), true);
    fixture.invoke("restoreDefaults");
    verifyOnlyPageReturnedToDefault(draft, page);
    QCOMPARE(fixture.window()->property("defaultsEnabled").toBool(), false);
}

void TestSettingsApply::walletUnavailableState()
{
    QVERIFY(qEnvironmentVariableIntValue("KONDOR_NO_KWALLET") != 0);
    SettingsWindowFixture fixture(m_engine);
    QVERIFY(fixture.window());
    QVERIFY(fixture.showExposed());
    fixture.window()->setProperty("currentPage", 4);
    QTRY_COMPARE(PasswordStore::instance()->state(), QStringLiteral("unavailable"));
}

int runTestSettingsApply(int argc, char *argv[])
{
    TestSettingsApply test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_settingsapply.moc"
