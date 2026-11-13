#include "tabstripharness.h"

class TestTabDrag : public TabStripFixture
{
    Q_OBJECT

private slots:
    void initTestCase() { registerTabStripTypes(); }
    void init() { setUpStrip(); }
    void cleanup() { tearDownStrip(); }
    void draggedTabFollowsThePointerAndSelectsItself();
    void draggedTabSwapsPastTheCenterOfItsNeighbour();
    void draggedTabSwapsAgainPastTheNextCenter();
    void releasingKeepsTheNewOrderAndSelection();
    void draggedTabIsClampedToTheStrip();
    void pinnedTabsStayInTheirSection();

private:
    DragSession pressFifthOfFiveTabsSelected();
    void releaseAndSettle(const DragSession &session, int dx);
    int halfWidth() const { return int(tabWidth() / 2); }
    void dragToTheLeftEdge(const DragSession &session);
    void dragToTheRightEdge(const DragSession &session);
};

DragSession TestTabDrag::pressFifthOfFiveTabsSelected()
{
    addTabs(5);
    m_tabs->setCurrentIndex(4);
    return pressOnTab(1, 100);
}

void TestTabDrag::releaseAndSettle(const DragSession &session, int dx)
{
    releaseDrag(session, dx);
    waitForSlotAnimation(session);
}

void TestTabDrag::draggedTabFollowsThePointerAndSelectsItself()
{
    const DragSession session = pressFifthOfFiveTabsSelected();
    dragBy(session, halfWidth() - 5);
    verifyDraggedLeftIs(session, session.startLeft + halfWidth() - 5);
    QCOMPARE(order(), session.before);
    QCOMPARE(m_tabs->currentTab(), session.before[1]);
    releaseAndSettle(session, halfWidth() - 5);
}

void TestTabDrag::draggedTabSwapsPastTheCenterOfItsNeighbour()
{
    const DragSession session = pressFifthOfFiveTabsSelected();
    dragBy(session, halfWidth() + 5);
    QCOMPARE(tabAt(1), session.before[2]);
    QCOMPARE(tabAt(2), session.before[1]);
    verifyDraggedLeftIs(session, session.startLeft + halfWidth() + 5);
    releaseAndSettle(session, halfWidth() + 5);
}

void TestTabDrag::draggedTabSwapsAgainPastTheNextCenter()
{
    const DragSession session = pressFifthOfFiveTabsSelected();
    const int target = int(tabWidth() * 1.5);
    dragBy(session, target - 5);
    QCOMPARE(tabAt(2), session.before[1]);
    dragBy(session, target + 5);
    QCOMPARE(tabAt(3), session.before[1]);
    verifyDraggedLeftIs(session, session.startLeft + target + 5);
    releaseAndSettle(session, target + 5);
}

void TestTabDrag::releasingKeepsTheNewOrderAndSelection()
{
    const DragSession session = pressFifthOfFiveTabsSelected();
    const int target = int(tabWidth() * 1.5) + 5;
    dragBy(session, target);
    releaseDrag(session, target);
    waitForSlotAnimation(session);
    QCOMPARE(tabAt(3), session.before[1]);
    QCOMPARE(m_tabs->currentTab(), session.before[1]);
}

void TestTabDrag::dragToTheLeftEdge(const DragSession &session)
{
    for (int dx = -10; session.press.x() + dx > 2; dx -= 10)
        QTest::mouseMove(m_window, session.press + QPoint(dx, 0));
    QTest::qWait(100);
}

void TestTabDrag::dragToTheRightEdge(const DragSession &session)
{
    for (int dx = -session.press.x() + 5; dx <= 1090 - session.press.x(); dx += 20)
        QTest::mouseMove(m_window, session.press + QPoint(dx, 0));
    QTest::qWait(100);
}

void TestTabDrag::draggedTabIsClampedToTheStrip()
{
    addTabs(5);
    const qreal first = leftOf(0);
    const qreal last = leftOf(4);
    const DragSession session = pressOnTab(3, 100);
    dragToTheLeftEdge(session);
    QCOMPARE(tabAt(0), session.before[3]);
    verifyDraggedLeftIs(session, first);
    dragToTheRightEdge(session);
    QCOMPARE(tabAt(4), session.before[3]);
    verifyDraggedLeftIs(session, last);
    releaseDrag(session, 1090 - session.press.x());
    waitForSlotAnimation(session);
}

void TestTabDrag::pinnedTabsStayInTheirSection()
{
    addTabs(5);
    m_tabs->setPinned(0, true);
    m_tabs->setPinned(1, true);
    QTest::qWait(100);
    const DragSession session = pressOnTab(0, 18);
    for (int dx = 0; dx <= 400; dx += 20)
        QTest::mouseMove(m_window, session.press + QPoint(dx, 0));
    QTest::qWait(100);
    QCOMPARE(tabAt(1), session.before[0]);
    QCOMPARE(tabAt(2), session.before[2]);
    releaseDrag(session, 400);
    QTest::qWait(100);
    QVERIFY(tabAt(0)->pinned() && tabAt(1)->pinned());
}

int runTabDrag(int argc, char *argv[])
{
    TestTabDrag test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_tabdrag.moc"
