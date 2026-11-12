#include "tabstripharness.h"

class TestTabDragScroll : public TabStripFixture
{
    Q_OBJECT

private slots:
    void initTestCase() { registerTabStripTypes(); }
    void init() { setUpStrip(); }
    void cleanup() { tearDownStrip(); }
    void draggingInAScrolledStripGoesTheRightWay();
    void draggingToTheEdgeAutoScrolls();
    void leavingTheEdgeZoneStopsTheScrolling();

private:
    void scrollThirtyTabsToTheEnd();
    void scrollThirtyTabsToTheStart();
    DragSession pressTabOfThirtyScrolledToTheEnd();
    DragSession pressSecondOfThirtyAndReachTheRightEdge();
    void waitForAutoScrollToTheEnd(const DragSession &session);
};

void TestTabDragScroll::scrollThirtyTabsToTheEnd()
{
    resizeStrip(1100);
    addTabs(30);
    const qreal maxScroll = m_strip->property("maxScroll").toReal();
    QVERIFY(maxScroll > 0);
    scrollTo(maxScroll);
    QTRY_COMPARE(scrolled(), maxScroll);
}

DragSession TestTabDragScroll::pressTabOfThirtyScrolledToTheEnd()
{
    scrollThirtyTabsToTheEnd();
    return pressOnTab(27, 30);
}

void TestTabDragScroll::draggingInAScrolledStripGoesTheRightWay()
{
    const DragSession session = pressTabOfThirtyScrolledToTheEnd();
    for (int dx = -10; dx >= -130; dx -= 10)
        QTest::mouseMove(m_window, session.press + QPoint(dx, 0));
    QTest::qWait(100);
    QCOMPARE(tabAt(26), session.before[27]);
    verifyDraggedLeftIs(session, session.startLeft - 130);
    releaseDrag(session, -130);
    waitForSlotAnimation(session);
}

void TestTabDragScroll::scrollThirtyTabsToTheStart()
{
    resizeStrip(1100);
    addTabs(30);
    scrollTo(0.0);
    QTRY_COMPARE(scrolled(), 0.0);
}

DragSession TestTabDragScroll::pressSecondOfThirtyAndReachTheRightEdge()
{
    scrollThirtyTabsToTheStart();
    const DragSession session = pressOnTab(1, 30);
    const int viewWidth = int(view()->width());
    for (int x = session.press.x(); x < viewWidth - 10; x += 20)
        QTest::mouseMove(m_window, QPoint(x, kStripRowY));
    QTest::mouseMove(m_window, QPoint(viewWidth - 10, kStripRowY));
    return session;
}

void TestTabDragScroll::waitForAutoScrollToTheEnd(const DragSession &session)
{
    const qreal maxScroll = m_strip->property("maxScroll").toReal();
    QTRY_VERIFY_WITH_TIMEOUT(scrolled() > 50, 2000);
    QTRY_COMPARE_WITH_TIMEOUT(scrolled(), maxScroll, 10000);
    QTRY_COMPARE(tabAt(29), session.before[1]);
}

void TestTabDragScroll::draggingToTheEdgeAutoScrolls()
{
    const DragSession session = pressSecondOfThirtyAndReachTheRightEdge();
    waitForAutoScrollToTheEnd(session);
    QVERIFY(qAbs(leftOfItem(session.dragged) - leftOf(29)) <= 1.0);
}

void TestTabDragScroll::leavingTheEdgeZoneStopsTheScrolling()
{
    const DragSession session = pressSecondOfThirtyAndReachTheRightEdge();
    waitForAutoScrollToTheEnd(session);
    const QPoint middle(int(view()->width()) / 2, kStripRowY);
    QTest::mouseMove(m_window, middle);
    QTest::qWait(100);
    const qreal stopped = scrolled();
    QTest::qWait(150);
    QCOMPARE(scrolled(), stopped);
    QTest::mouseRelease(m_window, Qt::LeftButton, {}, middle);
    waitForSlotAnimation(session);
}

int runTabDragScroll(int argc, char *argv[])
{
    TestTabDragScroll test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_tabdragscroll.moc"
