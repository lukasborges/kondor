#include <QAccessible>
#include "extensionsuiharness.h"

class TestExtensionsPanel : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanup();
    void listShowsOneRowPerExtension();
    void rowIsDimmedWhenOffOnSite();
    void rowOpensActions();
    void backReturnsToListAndFocusesRow();
    void actionKeepsPanelOpen();
    void checkableActionShowsState();
    void runOnSiteSwitchShowsReloadBar();
    void privateTabHasNoSiteSwitchAndNoPin();
    void openAtShowsActions();
    void pinButtonTogglesPin();

private:
    void openPanel(const QString &extensionId = QString());
    QQuickItem *rowAt(int index) const;
    QQuickItem *panelItem(const char *name) const;
    QString currentId() const;

    QTemporaryDir m_work;
    QQmlEngine m_engine;
    std::unique_ptr<Tab> m_tab;
    QScopedPointer<QObject> m_window;
    QObject *m_panel = nullptr;
};

void TestExtensionsPanel::initTestCase()
{
    QVERIFY(m_work.isValid());
}

void TestExtensionsPanel::cleanup()
{
    m_window.reset();
    m_tab.reset();
    m_engine.rootContext()->setContextProperty(QStringLiteral("theTab"), nullptr);
    removeEveryExtension();
}

void TestExtensionsPanel::openPanel(const QString &extensionId)
{
    if (ExtensionManager::instance()->count() == 0)
        QVERIFY(installSample(m_work.path()));
    if (!m_tab) {
        m_tab.reset(new Tab(nullptr));
        m_tab->setUrl(QUrl(QStringLiteral("https://www.example.com/page")));
        m_tab->extensionItems()->setChecked(QStringLiteral("sample"), QStringLiteral("toggle"), true);
    }
    m_engine.rootContext()->setContextProperty(QStringLiteral("theTab"), m_tab.get());
    m_window.reset(createInWindow(&m_engine, panelWindowQml));
    QVERIFY(m_window);
    m_panel = childObject(m_window.data(), "panel");
    if (extensionId.isEmpty())
        QMetaObject::invokeMethod(m_panel, "open");
    else
        QMetaObject::invokeMethod(m_panel, "openAt", Q_ARG(QVariant, extensionId));
    QTRY_VERIFY(m_panel->property("opened").toBool());
}

QQuickItem *TestExtensionsPanel::panelItem(const char *name) const
{
    return findByName(m_window.data(), name);
}

QQuickItem *TestExtensionsPanel::rowAt(int index) const
{
    QQuickItem *row = nullptr;
    QMetaObject::invokeMethod(panelItem("panelExtensionList"), "itemAtIndex",
                              Q_RETURN_ARG(QQuickItem *, row), Q_ARG(int, index));
    return row;
}

QString TestExtensionsPanel::currentId() const
{
    return m_panel->property("currentId").toString();
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
    clickCenterOf(panelItem("siteSwitch"));
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

int runTestExtensionsPanel(int argc, char *argv[])
{
    TestExtensionsPanel test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensionspanel.moc"
