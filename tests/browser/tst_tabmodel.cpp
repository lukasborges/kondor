#include <QGuiApplication>
#include <QSignalSpy>
#include <QStandardPaths>
#include <QTest>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "browser/profilemanager.h"
#include "browser/tab.h"
#include "browser/tabmodel.h"

class TestTabModel : public QObject
{
    Q_OBJECT

private slots:
    void startsEmpty();
    void addsAndActivatesTabs();
    void closingCurrentMiddleSelectsNext();
    void closingCurrentLastSelectsPrevious();
    void closingBeforeCurrentShiftsIndex();
    void closingAllTabsClearsCurrent();
    void setCurrentIndexIgnoresOutOfRange();
    void privateTabUsesAnotherProfile();
    void privateWindowKeepsEveryTabPrivate();
    void reopenClosedTabRestoresPosition();
    void privateTabsAreNotReopened();
    void recentlyClosedListsNewestFirst();
    void reopenClosedTabByIndex();
    void privateTabsAreNotInRecentlyClosed();
    void tabsStartOnNewTabPage();
    void emptyNavigationDoesNothing();
    void navigateLeavesNewTabPage();
    void showNewTabPageRestoresIt();
    void aboutBlankKeepsNewTabPage();
    void closedNewTabPageIsNotRemembered();
    void pinningMovesTabToEndOfPinnedGroup();
    void unpinningMovesTabToStartOfUnpinnedTabs();
    void moveTabKeepsTheCurrentTabSelected();
    void recentlyClosedKeepsAtMostTheLimit();
};

void TestTabModel::startsEmpty()
{
    TabModel model;
    QCOMPARE(model.count(), 0);
    QCOMPARE(model.currentIndex(), -1);
    QVERIFY(!model.currentTab());
}

void TestTabModel::addsAndActivatesTabs()
{
    TabModel model;

    model.addTab();
    QCOMPARE(model.count(), 1);
    QCOMPARE(model.currentIndex(), 0);

    model.addTab();
    model.addTab();
    QCOMPARE(model.count(), 3);
    QCOMPARE(model.currentIndex(), 2);
    QVERIFY(model.currentTab());
}

void TestTabModel::closingCurrentMiddleSelectsNext()
{
    TabModel model;
    Tab *first = model.addTab();
    Tab *second = model.addTab();
    Tab *third = model.addTab();
    QCOMPARE(model.currentIndex(), 2);

    model.setCurrentIndex(1);
    QCOMPARE(model.currentTab(), second);

    model.closeTab(1);
    QCOMPARE(model.count(), 2);
    QCOMPARE(model.currentIndex(), 1);
    QCOMPARE(model.currentTab(), third);
    QVERIFY(model.indexOfTab(first) == 0);
}

void TestTabModel::closingCurrentLastSelectsPrevious()
{
    TabModel model;
    Tab *first = model.addTab();
    model.addTab();
    QCOMPARE(model.currentIndex(), 1);

    model.closeTab(1);
    QCOMPARE(model.count(), 1);
    QCOMPARE(model.currentIndex(), 0);
    QCOMPARE(model.currentTab(), first);
}

void TestTabModel::closingBeforeCurrentShiftsIndex()
{
    TabModel model;
    Tab *first = model.addTab();
    Tab *second = model.addTab();
    Tab *third = model.addTab();
    model.setCurrentIndex(2);

    model.closeTab(0);
    QCOMPARE(model.count(), 2);
    QCOMPARE(model.currentIndex(), 1);
    QCOMPARE(model.currentTab(), third);
    QCOMPARE(model.indexOfTab(second), 0);
    QCOMPARE(model.indexOfTab(first), -1);
}

void TestTabModel::closingAllTabsClearsCurrent()
{
    TabModel model;
    model.addTab();
    model.addTab();

    model.closeTab(0);
    model.closeTab(0);
    QCOMPARE(model.count(), 0);
    QCOMPARE(model.currentIndex(), -1);
    QVERIFY(!model.currentTab());
}

void TestTabModel::setCurrentIndexIgnoresOutOfRange()
{
    TabModel model;
    model.addTab();
    model.addTab();
    QCOMPARE(model.currentIndex(), 1);

    model.setCurrentIndex(2);
    QCOMPARE(model.currentIndex(), 1);
    model.setCurrentIndex(-1);
    QCOMPARE(model.currentIndex(), 1);
}

void TestTabModel::privateTabUsesAnotherProfile()
{
    TabModel model;
    Tab *normal = model.addTab(false);
    Tab *privateTab = model.addTab(true);

    QVERIFY(normal);
    QVERIFY(privateTab);
    QVERIFY(!normal->isPrivate());
    QVERIFY(privateTab->isPrivate());
    QVERIFY(privateTab->profile());
    QVERIFY(privateTab->profile()->isOffTheRecord());
    QVERIFY(privateTab->profile() != normal->profile());
}

void TestTabModel::privateWindowKeepsEveryTabPrivate()
{
    TabModel model;
    model.setPrivateTabs(true);

    // Even a caller that asks for a normal tab, or hands in the persistent
    // profile, gets a private tab from a private window.
    Tab *fromAddTab = model.addTab(false);
    Tab *fromProfile = model.addTabWithProfile(
        ProfileManager::instance()->defaultProfile(),
        QUrl(QStringLiteral("https://private.example")), false);

    QVERIFY(fromAddTab);
    QVERIFY(fromProfile);
    QVERIFY(fromAddTab->isPrivate());
    QVERIFY(fromProfile->isPrivate());
    QVERIFY(fromProfile->profile()->isOffTheRecord());
}

void TestTabModel::reopenClosedTabRestoresPosition()
{
    TabModel model;
    model.addTab(false, QUrl(QStringLiteral("https://a.example")));
    model.addTab(false, QUrl(QStringLiteral("https://b.example")));
    model.addTab(false, QUrl(QStringLiteral("https://c.example")));
    QVERIFY(!model.canReopenClosedTab());

    model.closeTab(1);
    QCOMPARE(model.count(), 2);
    QVERIFY(model.canReopenClosedTab());

    model.reopenClosedTab();
    QCOMPARE(model.count(), 3);
    QCOMPARE(model.currentIndex(), 1);
    QCOMPARE(model.currentTab()->url(), QUrl(QStringLiteral("https://b.example")));
    QVERIFY(!model.canReopenClosedTab());
}

void TestTabModel::recentlyClosedListsNewestFirst()
{
    TabModel model;
    QSignalSpy spy(&model, &TabModel::recentlyClosedChanged);
    model.addTab(false, QUrl(QStringLiteral("https://a.example")));
    model.addTab(false, QUrl(QStringLiteral("https://b.example")));
    model.addTab(false, QUrl(QStringLiteral("https://c.example")));
    QVERIFY(model.recentlyClosed().isEmpty());

    model.closeTab(0);
    model.closeTab(1);
    QCOMPARE(spy.count(), 2);

    const QVariantList closed = model.recentlyClosed();
    QCOMPARE(closed.size(), 2);
    QCOMPARE(closed.at(0).toMap().value(QStringLiteral("url")).toUrl(),
             QUrl(QStringLiteral("https://c.example")));
    QCOMPARE(closed.at(1).toMap().value(QStringLiteral("url")).toUrl(),
             QUrl(QStringLiteral("https://a.example")));
}

void TestTabModel::reopenClosedTabByIndex()
{
    TabModel model;
    model.addTab(false, QUrl(QStringLiteral("https://a.example")));
    model.addTab(false, QUrl(QStringLiteral("https://b.example")));
    model.addTab(false, QUrl(QStringLiteral("https://c.example")));
    model.closeTab(0);
    model.closeTab(1);

    // Index 1 is the older one (a.example); c.example stays in the list.
    model.reopenClosedTab(1);
    QCOMPARE(model.currentTab()->url(), QUrl(QStringLiteral("https://a.example")));
    QCOMPARE(model.recentlyClosed().size(), 1);
    QCOMPARE(model.recentlyClosed().at(0).toMap().value(QStringLiteral("url")).toUrl(),
             QUrl(QStringLiteral("https://c.example")));

    model.reopenClosedTab(5);
    QCOMPARE(model.recentlyClosed().size(), 1);
}

void TestTabModel::privateTabsAreNotInRecentlyClosed()
{
    TabModel model;
    model.addTab(false, QUrl(QStringLiteral("https://a.example")));
    model.addTab(true, QUrl(QStringLiteral("https://private.example")));
    model.closeTab(1);
    QVERIFY(model.recentlyClosed().isEmpty());
}

void TestTabModel::privateTabsAreNotReopened()
{
    TabModel model;
    model.addTab(false, QUrl(QStringLiteral("https://a.example")));
    model.addTab(true, QUrl(QStringLiteral("https://private.example")));

    model.closeTab(1);
    QCOMPARE(model.count(), 1);
    QVERIFY(!model.canReopenClosedTab());

    model.reopenClosedTab();
    QCOMPARE(model.count(), 1);
}

void TestTabModel::tabsStartOnNewTabPage()
{
    TabModel model;
    Tab *tab = model.addTab();
    QVERIFY(tab->newTabPage());
    QVERIFY(tab->url().isEmpty());
}

void TestTabModel::emptyNavigationDoesNothing()
{
    TabModel model;
    Tab *tab = model.addTab();
    QSignalSpy navigationSpy(tab, &Tab::navigationRequested);

    tab->navigateTo(QUrl());
    QCOMPARE(navigationSpy.count(), 0);
    QVERIFY(tab->newTabPage());
}

void TestTabModel::navigateLeavesNewTabPage()
{
    TabModel model;
    Tab *tab = model.addTab();
    tab->navigateTo(QUrl(QStringLiteral("https://a.example")));
    QVERIFY(!tab->newTabPage());
}

void TestTabModel::showNewTabPageRestoresIt()
{
    TabModel model;
    Tab *tab = model.addTab(false, QUrl(QStringLiteral("https://a.example")));
    QVERIFY(!tab->newTabPage());

    QSignalSpy pageSpy(tab, &Tab::newTabPageRequested);
    tab->showNewTabPage();
    QVERIFY(tab->newTabPage());
    QCOMPARE(pageSpy.count(), 1);
}

void TestTabModel::aboutBlankKeepsNewTabPage()
{
    TabModel model;
    Tab *tab = model.addTab();
    // showNewTabPage() loads about:blank; the native page stays on screen.
    tab->setUrl(QUrl(QStringLiteral("about:blank")));
    QVERIFY(tab->newTabPage());
}

void TestTabModel::closedNewTabPageIsNotRemembered()
{
    TabModel model;
    model.addTab(false, QUrl(QStringLiteral("https://a.example")));
    model.addTab();
    model.closeTab(1);
    QVERIFY(!model.canReopenClosedTab());
}

void TestTabModel::pinningMovesTabToEndOfPinnedGroup()
{
    TabModel model;
    Tab *first = model.addTab();
    Tab *second = model.addTab();
    Tab *third = model.addTab();

    model.setPinned(0, true);
    model.setPinned(2, true);

    QCOMPARE(model.pinnedCount(), 2);
    QCOMPARE(model.indexOfTab(first), 0);
    QCOMPARE(model.indexOfTab(third), 1);
    QCOMPARE(model.indexOfTab(second), 2);
}

void TestTabModel::unpinningMovesTabToStartOfUnpinnedTabs()
{
    TabModel model;
    Tab *first = model.addTab();
    Tab *second = model.addTab();
    Tab *third = model.addTab();
    model.setPinned(0, true);
    model.setPinned(1, true);

    model.setPinned(0, false);

    QCOMPARE(model.pinnedCount(), 1);
    QCOMPARE(model.indexOfTab(second), 0);
    QCOMPARE(model.indexOfTab(first), 1);
    QCOMPARE(model.indexOfTab(third), 2);
}

void TestTabModel::moveTabKeepsTheCurrentTabSelected()
{
    TabModel model;
    model.addTab();
    Tab *second = model.addTab();
    model.addTab();
    model.setCurrentIndex(1);

    model.moveTab(0, 2);

    QCOMPARE(model.currentTab(), second);
    QCOMPARE(model.currentIndex(), 0);
}

void TestTabModel::recentlyClosedKeepsAtMostTheLimit()
{
    TabModel model;
    for (int i = 0; i < 25; ++i)
        model.addTab(false, QUrl(QStringLiteral("https://site%1.example/").arg(i)));
    for (int i = 0; i < 25; ++i)
        model.closeTab(0);

    const QVariantList closed = model.recentlyClosed();
    QCOMPARE(closed.size(), 20);
    QCOMPARE(closed.first().toMap().value(QStringLiteral("url")).toUrl(),
             QUrl(QStringLiteral("https://site24.example/")));
}

int main(int argc, char *argv[])
{
    // Keep the persistent test profile out of the real user directories.
    QStandardPaths::setTestModeEnabled(true);
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();

    QGuiApplication app(argc, argv);
    TestTabModel test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_tabmodel.moc"
