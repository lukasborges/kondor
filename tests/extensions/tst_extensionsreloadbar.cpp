#include "panelfixture.h"

class TestExtensionsReloadBar : public QObject, private PanelFixture
{
    Q_OBJECT

private slots:
    void initTestCase() { QVERIFY(m_work.isValid()); }
    void cleanup() { resetPanel(); }
    void reloadButtonRequestsReload();
    void startingToLoadHidesReloadBar();
    void togglingBackHidesReloadBar();
};

void TestExtensionsReloadBar::reloadButtonRequestsReload()
{
    openPanel(QStringLiteral("sample"));
    QSignalSpy reloads(m_tab.get(), &Tab::reloadRequested);
    toggleRunOnSite();
    QQuickItem *button = nullptr;
    QTRY_VERIFY((button = itemWithText(panelItem("bar"), QStringLiteral("Reload"))));
    clickCenterOf(button);
    QCOMPARE(reloads.count(), 1);
}

void TestExtensionsReloadBar::startingToLoadHidesReloadBar()
{
    openPanel(QStringLiteral("sample"));
    toggleRunOnSite();
    m_tab->setLoading(true);
    QVERIFY(!panelItem("bar")->isVisible());
}

void TestExtensionsReloadBar::togglingBackHidesReloadBar()
{
    openPanel(QStringLiteral("sample"));
    toggleRunOnSite();
    toggleRunOnSite();
    QVERIFY(!panelItem("bar")->isVisible());
}

int runTestExtensionsReloadBar(int argc, char *argv[])
{
    TestExtensionsReloadBar test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensionsreloadbar.moc"
