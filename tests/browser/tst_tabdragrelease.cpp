#include "tabstripharness.h"

class TestTabDragRelease : public TabStripFixture
{
    Q_OBJECT

private slots:
    void initTestCase() { registerTabStripTypes(); }
    void init() { setUpStrip(); }
    void cleanup() { tearDownStrip(); }
    void shortMoveIsAClick();
    void closingAfterAClickDoesNotCrash();
    void releaseAnimatesIntoTheSlot();
    void currentTabIsVisibleAfterARelease();
    void closingTheDraggedTabResetsTheDragState();

private:
    void clickCloseButtonOf(int index);
    void closeAccordingToVariant(int variant);
    void dragRightByFiveStepsUpTo(const DragSession &session, int maxDx);
    void verifyCurrentTabIsInsideTheView();
};

void TestTabDragRelease::shortMoveIsAClick()
{
    addTabs(5);
    const DragSession session = pressOnTab(1, 100);
    QTest::mouseMove(m_window, session.press + QPoint(2, 0));
    releaseDrag(session, 2);
    QTest::qWait(50);
    QCOMPARE(order(), session.before);
    QCOMPARE(m_tabs->currentIndex(), 1);
}

void TestTabDragRelease::clickCloseButtonOf(int index)
{
    QTest::mouseClick(m_window, Qt::LeftButton, {},
                      QPoint(int(leftOf(index) + tabWidth()) - 14, kStripRowY));
}

void TestTabDragRelease::closeAccordingToVariant(int variant)
{
    if (variant == 0)
        clickCloseButtonOf(1);
    else if (variant == 1)
        clickCloseButtonOf(2);
    else
        QTest::mouseClick(m_window, Qt::MiddleButton, {}, QPoint(int(leftOf(2)) + 60, kStripRowY));
}

void TestTabDragRelease::closingAfterAClickDoesNotCrash()
{
    for (int variant = 0; variant < 4; ++variant) {
        restartStrip();
        addTabs(5);
        m_tabs->setCurrentIndex(variant < 3 ? 4 : 1);
        QTest::mouseClick(m_window, Qt::LeftButton, {}, QPoint(int(leftOf(1)) + 60, kStripRowY));
        QTest::qWait(1000);
        closeAccordingToVariant(variant);
        QTest::qWait(300);
        QCOMPARE(m_tabs->count(), 4);
    }
}

void TestTabDragRelease::dragRightByFiveStepsUpTo(const DragSession &session, int maxDx)
{
    for (int dx = 5; dx <= maxDx; dx += 5)
        QTest::mouseMove(m_window, session.press + QPoint(dx, 0));
    QTest::qWait(60);
}

void TestTabDragRelease::releaseAnimatesIntoTheSlot()
{
    addTabs(5);
    const DragSession session = pressOnTab(1, 100);
    dragRightByFiveStepsUpTo(session, 40);
    QVERIFY(session.dragged->property("dragShift").toReal() != 0.0);
    releaseDrag(session, 40);
    QVERIFY(session.dragged->property("dragShift").toReal() != 0.0);
    waitForSlotAnimation(session);
}

void TestTabDragRelease::verifyCurrentTabIsInsideTheView()
{
    QQuickItem *current = itemAt(m_tabs->currentIndex());
    QTRY_VERIFY(current->mapToItem(view(), QPointF(0, 0)).x() >= -0.5
                && current->mapToItem(view(), QPointF(current->width(), 0)).x()
                    <= view()->width() + 0.5);
}

void TestTabDragRelease::currentTabIsVisibleAfterARelease()
{
    resizeStrip(1100);
    addTabs(30);
    scrollTo(253.0);
    QTRY_COMPARE(scrolled(), 253.0);
    int index = 0;
    while (index < 29 && leftOf(index) < 40)
        ++index;
    const QPoint press(int(leftOf(index)) + int(tabWidth()) - 30, kStripRowY);
    QTest::mousePress(m_window, Qt::LeftButton, {}, press);
    for (int x = press.x(); x > 40; x -= 10)
        QTest::mouseMove(m_window, QPoint(x, kStripRowY));
    QTest::mouseMove(m_window, QPoint(40, kStripRowY));
    QTest::qWait(60);
    QTest::mouseRelease(m_window, Qt::LeftButton, {}, QPoint(40, kStripRowY));
    verifyCurrentTabIsInsideTheView();
}

void TestTabDragRelease::closingTheDraggedTabResetsTheDragState()
{
    addTabs(5);
    const DragSession session = pressOnTab(1, 100);
    dragRightByFiveStepsUpTo(session, 60);
    QVERIFY(m_strip->property("tabDragActive").toBool());
    m_tabs->closeTabObject(tabAt(m_tabs->currentIndex()));
    releaseDrag(session, 60);
    QTest::qWait(300);
    QCOMPARE(m_strip->property("tabDragActive").toBool(), false);
    QCOMPARE(m_tabs->count(), 4);
}

int runTabDragRelease(int argc, char *argv[])
{
    TestTabDragRelease test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_tabdragrelease.moc"
