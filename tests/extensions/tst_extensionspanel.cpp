#include <QAccessible>
#include "panelfixture.h"

class TestExtensionsPanel : public QObject, private PanelFixture
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanup() { resetPanel(); }
    void listShowsOneRowPerExtension();
    void rowIsDimmedWhenOffOnSite();
    void rowOpensActions();
    void backReturnsToListAndFocusesRow();
    void actionKeepsPanelOpen();
    void checkableActionShowsState();
    void runOnSiteSwitchShowsReloadBar();
    void privateTabHasNoSiteSwitchAndNoPin();
    void hostIsHiddenOnNonWebPage();
    void openAtShowsActions();
    void pinButtonTogglesPin();
    void actionRowShowsShortcut();
    void checkableRowShowsShortcut();
    void shortcutFollowsChangedSetting();
};

void TestExtensionsPanel::initTestCase()
{
    QVERIFY(m_work.isValid());
}

void TestExtensionsPanel::listShowsOneRowPerExtension()
{
    QVERIFY(installSample(m_work.path()));
    QVERIFY(installNamed(m_work.path(), QStringLiteral("alpha"), QStringLiteral("Alpha")));
    openPanel();
    QQuickItem *list = panelItem("panelExtensionList");
    QVERIFY(list);
    QCOMPARE(list->property("count").toInt(), 2);
    QTRY_VERIFY(rowAt(0));
    QCOMPARE(QAccessible::queryAccessibleInterface(rowAt(0))->text(QAccessible::Name), QStringLiteral("Alpha"));
}

void TestExtensionsPanel::rowIsDimmedWhenOffOnSite()
{
    QVERIFY(installSample(m_work.path()));
    openPanel();
    ExtensionManager::instance()->setSiteEnabled(QStringLiteral("sample"), m_tab->url(), false);
    QTRY_VERIFY(rowAt(0));
    QQuickItem *row = rowAt(0);
    const QList<QQuickItem *> parts = row->property("contentItem").value<QQuickItem *>()->childItems();
    QTRY_VERIFY(!parts.at(0)->isEnabled());
    QVERIFY(!parts.at(1)->isEnabled());
    QVERIFY(row->isEnabled());
    QCOMPARE(QAccessible::queryAccessibleInterface(row)->text(QAccessible::Name),
             QStringLiteral("Sample Extension, off on www.example.com"));
}

void TestExtensionsPanel::rowOpensActions()
{
    openPanel();
    QTRY_VERIFY(rowAt(0));
    clickCenterOf(rowAt(0));
    QCOMPARE(currentId(), QStringLiteral("sample"));
    QVERIFY(itemWithText(panelItem("backButton")->parentItem(), QStringLiteral("Sample Extension")));
}

void TestExtensionsPanel::backReturnsToListAndFocusesRow()
{
    openPanel(QStringLiteral("sample"));
    clickCenterOf(panelItem("backButton"));
    QCOMPARE(currentId(), QString());
    QTRY_VERIFY(rowAt(0) && rowAt(0)->hasActiveFocus());
}

void TestExtensionsPanel::actionKeepsPanelOpen()
{
    QVERIFY(installPlain(m_work.path()));
    openPanel(QStringLiteral("plain"));
    QSignalSpy triggers(m_tab->extensionItems(), &TabExtensionItems::triggered);
    QQuickItem *action = itemWithText(panelItem("backButton")->parentItem()->parentItem(), QStringLiteral("Go Now"));
    QVERIFY(action);
    clickCenterOf(action);
    QCOMPARE(triggers.count(), 1);
    QVERIFY(m_panel->property("opened").toBool());
}

void TestExtensionsPanel::checkableActionShowsState()
{
    openPanel(QStringLiteral("sample"));
    QQuickItem *box = itemWithText(panelItem("backButton")->parentItem()->parentItem(), QStringLiteral("Toggle Mark"));
    QVERIFY(box);
    QVERIFY(box->property("checked").toBool());
    m_tab->extensionItems()->setChecked(QStringLiteral("sample"), QStringLiteral("toggle"), false);
    QTRY_VERIFY(!box->property("checked").toBool());
}

void TestExtensionsPanel::runOnSiteSwitchShowsReloadBar()
{
    openPanel(QStringLiteral("sample"));
    QSignalSpy reloads(m_tab.get(), &Tab::reloadRequested);
    toggleRunOnSite();
    QCOMPARE(reloads.count(), 0);
    QVERIFY(!ExtensionManager::instance()->siteEnabled(QStringLiteral("sample"), m_tab->url()));
    QVERIFY(panelItem("bar")->isVisible());
    QVERIFY(itemWithText(panelItem("bar"), QStringLiteral("Sample Extension will stop running on this site after reloading.")));
}

void TestExtensionsPanel::privateTabHasNoSiteSwitchAndNoPin()
{
    QVERIFY(installSample(m_work.path()));
    allowInPrivateWindows(QStringLiteral("sample"));
    QQuickWebEngineProfile privateProfile;
    m_tab.reset(new Tab(&privateProfile));
    m_tab->setUrl(QUrl(QStringLiteral("https://www.example.com/page")));
    openPanel(QStringLiteral("sample"));
    QVERIFY(!panelItem("siteSwitch")->isVisible());
    QVERIFY(!panelItem("pinButton")->isVisible());
    m_window.reset();
    m_tab.reset();
}

void TestExtensionsPanel::hostIsHiddenOnNonWebPage()
{
    openPanel();
    QCOMPARE(m_panel->property("host").toString(), QStringLiteral("www.example.com"));
    m_tab->setUrl(QUrl(QStringLiteral("about:newtab")));
    QCOMPARE(m_panel->property("host").toString(), QString());
}

void TestExtensionsPanel::openAtShowsActions()
{
    openPanel(QStringLiteral("sample"));
    QCOMPARE(currentId(), QStringLiteral("sample"));
    QVERIFY(panelItem("backButton")->isVisible());
}

void TestExtensionsPanel::pinButtonTogglesPin()
{
    openPanel(QStringLiteral("sample"));
    clickCenterOf(panelItem("pinButton"));
    QVERIFY(ExtensionManager::instance()->isPinned(QStringLiteral("sample")));
    QVERIFY(m_panel->property("opened").toBool());
    clickCenterOf(panelItem("pinButton"));
    QVERIFY(!ExtensionManager::instance()->isPinned(QStringLiteral("sample")));
}

void TestExtensionsPanel::actionRowShowsShortcut()
{
    QVERIFY(installKeyed());
    openPanel(QStringLiteral("keyed"));
    QVERIFY(itemWithText(panelItem("backButton")->parentItem()->parentItem(), QKeySequence(QStringLiteral("S")).toString(QKeySequence::NativeText)));
}

void TestExtensionsPanel::checkableRowShowsShortcut()
{
    QVERIFY(installKeyed());
    openPanel(QStringLiteral("keyed"));
    QQuickItem *box = itemWithText(panelItem("backButton")->parentItem()->parentItem(), QStringLiteral("Mark"));
    QVERIFY(box);
    QCOMPARE(QAccessible::queryAccessibleInterface(box)->text(QAccessible::Description), QKeySequence(QStringLiteral("S")).toString(QKeySequence::NativeText));
}

void TestExtensionsPanel::shortcutFollowsChangedSetting()
{
    QVERIFY(installKeyed());
    openPanel(QStringLiteral("keyed"));
    applySettings(QStringLiteral("keyed"), {{QStringLiteral("keyGo"), QStringLiteral("Shift+F")}});
    const QString text = QKeySequence(QStringLiteral("Shift+F")).toString(QKeySequence::NativeText);
    QTRY_VERIFY(itemWithText(panelItem("backButton")->parentItem()->parentItem(), text));
}

int runTestExtensionsPanel(int argc, char *argv[])
{
    TestExtensionsPanel test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensionspanel.moc"
