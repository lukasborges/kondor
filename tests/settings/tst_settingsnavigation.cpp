#include "settingsnavigationharness.h"

class TestSettingsNavigation : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void init();
    void clickingSidebarSwitchesPages();
    void arrowKeysMoveBetweenPages();
    void searchFiltersPages();

private:
    QQmlEngine m_engine;
};

void TestSettingsNavigation::initTestCase()
{
    registerSettingsWindowTypes();
}

void TestSettingsNavigation::init()
{
    resetSettingsToTestDefaults();
}

void TestSettingsNavigation::clickingSidebarSwitchesPages()
{
    const QStringList titles{ QStringLiteral("General"), QStringLiteral("Search"),
                              QStringLiteral("Downloads"), QStringLiteral("Privacy") };
    SettingsWindowFixture fixture(m_engine);
    QVERIFY(fixture.window());
    QVERIFY(fixture.showExposed());
    verifyShownPage(fixture.window(), 0, titles[0]);
    for (int page = 0; page < titles.size(); ++page)
        clickSidebarEntryAndVerify(fixture.window(), page, titles[page]);
    fixture.invoke("discardChanges");
    QVERIFY(fixture.showExposed());
    verifyShownPage(fixture.window(), 3, titles[3]);
}

void TestSettingsNavigation::arrowKeysMoveBetweenPages()
{
    SettingsWindowFixture fixture(m_engine);
    QVERIFY(fixture.window());
    QVERIFY(fixture.showExposed());
    verifyShownPage(fixture.window(), 0, QStringLiteral("General"));
    QTest::keyClick(fixture.window(), Qt::Key_Down);
    verifyShownPage(fixture.window(), 1, QStringLiteral("Search"));
    QTest::keyClick(fixture.window(), Qt::Key_Down);
    verifyShownPage(fixture.window(), 2, QStringLiteral("Downloads"));
    QTest::keyClick(fixture.window(), Qt::Key_Up);
    verifyShownPage(fixture.window(), 1, QStringLiteral("Search"));
    QTest::keyClick(fixture.window(), Qt::Key_Escape);
    QVERIFY(!fixture.window()->isVisible());
}

void TestSettingsNavigation::searchFiltersPages()
{
    SettingsWindowFixture fixture(m_engine);
    QQuickWindow *window = fixture.window();
    QVERIFY(window);
    QVERIFY(fixture.showExposed());
    QCOMPARE(visiblePageCount(window), 7);
    QVERIFY(focusSearchField(window));
    searchFor(window, QStringLiteral("cookies"));
    verifyPrivacyIsTheOnlyEntry(window);
    searchFor(window, QStringLiteral("engine"));
    verifyOnlyPageIsListed(window, 1, QStringLiteral("Search"));
    searchFor(window, QStringLiteral("kwallet"));
    verifyOnlyPageIsListed(window, 4, QStringLiteral("Passwords"));
    searchFor(window, QString());
    QTRY_COMPARE(visiblePageCount(window), 7);
    verifyShownPage(window, 4, QStringLiteral("Passwords"));
}

int runTestSettingsNavigation(int argc, char *argv[])
{
    TestSettingsNavigation test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_settingsnavigation.moc"
