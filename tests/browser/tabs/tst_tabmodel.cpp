#include <QGuiApplication>
#include <QSignalSpy>
#include <QStandardPaths>
#include <QTemporaryDir>
#include <QTest>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "browser/profile/profilemanager.h"
#include "browser/tabs/tab.h"
#include "browser/tabs/tabmodel.h"
#include "../../common/isolatedhome.h"
#include "tabmodelharness.h"

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

int main(int argc, char *argv[])
{
    QStandardPaths::setTestModeEnabled(true);
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();

    QTemporaryDir home;
    if (!useIsolatedHome(home))
        return 1;

    QGuiApplication app(argc, argv);
    TestTabModel test;
    int failures = QTest::qExec(&test, argc, argv);
    failures |= runRecentlyClosedTabs(argc, argv);
    failures |= runTabNewTabPage(argc, argv);
    failures |= runTabPinning(argc, argv);
    return failures;
}

#include "tst_tabmodel.moc"
