#include <QSignalSpy>
#include <QTest>

#include "browser/profile/profilemanager.h"
#include "browser/tabs/tab.h"
#include "browser/tabs/tabmodel.h"
#include "tabmodelharness.h"

class TestTabNewTabPage : public QObject
{
    Q_OBJECT

private slots:
    void tabsStartOnNewTabPage();
    void emptyNavigationDoesNothing();
    void navigateLeavesNewTabPage();
    void showNewTabPageRestoresIt();
    void aboutBlankKeepsNewTabPage();
    void closedNewTabPageIsNotRemembered();
};

void TestTabNewTabPage::tabsStartOnNewTabPage()
{
    TabModel model;
    Tab *tab = model.addTab();
    QVERIFY(tab->newTabPage());
    QVERIFY(tab->url().isEmpty());
}

void TestTabNewTabPage::emptyNavigationDoesNothing()
{
    TabModel model;
    Tab *tab = model.addTab();
    QSignalSpy navigationSpy(tab, &Tab::navigationRequested);

    tab->navigateTo(QUrl());
    QCOMPARE(navigationSpy.count(), 0);
    QVERIFY(tab->newTabPage());
}

void TestTabNewTabPage::navigateLeavesNewTabPage()
{
    TabModel model;
    Tab *tab = model.addTab();
    tab->navigateTo(QUrl(QStringLiteral("https://a.example")));
    QVERIFY(!tab->newTabPage());
}

void TestTabNewTabPage::showNewTabPageRestoresIt()
{
    TabModel model;
    Tab *tab = model.addTab(false, QUrl(QStringLiteral("https://a.example")));
    QVERIFY(!tab->newTabPage());

    QSignalSpy pageSpy(tab, &Tab::newTabPageRequested);
    tab->showNewTabPage();
    QVERIFY(tab->newTabPage());
    QCOMPARE(pageSpy.count(), 1);
}

void TestTabNewTabPage::aboutBlankKeepsNewTabPage()
{
    TabModel model;
    Tab *tab = model.addTab();
    tab->setUrl(QUrl(QStringLiteral("about:blank")));
    QVERIFY(tab->newTabPage());
}

void TestTabNewTabPage::closedNewTabPageIsNotRemembered()
{
    TabModel model;
    model.addTab(false, QUrl(QStringLiteral("https://a.example")));
    model.addTab();
    model.closeTab(1);
    QVERIFY(!model.canReopenClosedTab());
}

int runTabNewTabPage(int argc, char *argv[])
{
    TestTabNewTabPage test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_tabnewtabpage.moc"
