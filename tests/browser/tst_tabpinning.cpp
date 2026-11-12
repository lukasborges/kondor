#include <QTest>

#include "browser/tab.h"
#include "browser/tabmodel.h"
#include "tabmodelharness.h"

class TestTabPinning : public QObject
{
    Q_OBJECT

private slots:
    void pinningMovesTabToEndOfPinnedGroup();
    void unpinningMovesTabToStartOfUnpinnedTabs();
    void moveTabKeepsTheCurrentTabSelected();
};

void TestTabPinning::pinningMovesTabToEndOfPinnedGroup()
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

void TestTabPinning::unpinningMovesTabToStartOfUnpinnedTabs()
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

void TestTabPinning::moveTabKeepsTheCurrentTabSelected()
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

int runTabPinning(int argc, char *argv[])
{
    TestTabPinning test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_tabpinning.moc"
