#include <QGuiApplication>
#include <QStandardPaths>
#include <QTest>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "tab.h"
#include "tabmodel.h"

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
