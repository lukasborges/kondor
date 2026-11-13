#include "tabstripharness.h"

class TestTabStripClosing : public TabStripFixture
{
    Q_OBJECT

private slots:
    void initTestCase() { registerTabStripTypes(); }
    void init() { setUpStrip(); }
    void cleanup() { tearDownStrip(); }
    void closingWithTheMouseKeepsTheWidth();
    void closingWithTheKeyboardRecomputesTheWidth();
    void widthStaysWhileThePointerIsOverTheStrip();
    void widthIsRecomputedWhenThePointerLeaves();

private:
    void closeWhileThePointerIsOverTheStrip();
};

void TestTabStripClosing::closingWithTheMouseKeepsTheWidth()
{
    addTabs(7);
    const qreal shrunk = tabWidth();
    QVERIFY(shrunk < 240.0);

    closeWithMouse(m_tabs->currentTab());
    QCOMPARE(m_tabs->count(), 6);
    QCOMPARE(tabWidth(), shrunk);
}

void TestTabStripClosing::closingWithTheKeyboardRecomputesTheWidth()
{
    addTabs(7);
    const qreal shrunk = tabWidth();
    closeWithMouse(m_tabs->currentTab());

    m_tabs->closeTab(0);
    QCOMPARE(m_tabs->count(), 5);
    QVERIFY(tabWidth() > shrunk);
}

void TestTabStripClosing::closeWhileThePointerIsOverTheStrip()
{
    QTest::mouseMove(m_window, QPoint(500, 10));
    closeWithMouse(m_tabs->currentTab());
    QTest::qWait(1200);
}

void TestTabStripClosing::widthStaysWhileThePointerIsOverTheStrip()
{
    addTabs(7);
    const qreal again = tabWidth();
    closeWhileThePointerIsOverTheStrip();
    QCOMPARE(tabWidth(), again);
}

void TestTabStripClosing::widthIsRecomputedWhenThePointerLeaves()
{
    addTabs(7);
    const qreal again = tabWidth();
    closeWhileThePointerIsOverTheStrip();
    QTest::mouseMove(m_window, QPoint(500, 58));
    QTRY_VERIFY(tabWidth() > again);
}

int runTabStripClosing(int argc, char *argv[])
{
    TestTabStripClosing test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_tabstripclosing.moc"
