#include "tabstripharness.h"

class TestTabStripWidths : public TabStripFixture
{
    Q_OBJECT

private slots:
    void initTestCase() { registerTabStripTypes(); }
    void init() { setUpStrip(); }
    void cleanup() { tearDownStrip(); }
    void fewTabsKeepTheStandardWidth();
    void newTabButtonFollowsTheLastTab();
    void tabsShrinkTogether();
    void titleDoesNotChangeTheWidth();
    void manyTabsStopAtTheMinimumAndShowScrollButtons();
    void scrollButtonsAreDisabledAtTheEnds();
    void currentTabIsScrolledIntoView();
    void pinnedTabsStayNarrow();
    void scrolledOutTabsAreClipped();
    void lastTabStaysClearOfTheRightButton();
    void firstTabStaysClearOfTheLeftButton();

private:
    void verifyTabIsVisible(int index);
    bool isInsideTabBar(int index) const;
    bool overlapsButton(int index, const char *buttonName) const;
};

void TestTabStripWidths::fewTabsKeepTheStandardWidth()
{
    addTabs(3);
    QCOMPARE(tabWidth(), 240.0);
    QVERIFY(!m_strip->property("overflowing").toBool());
    QVERIFY(!button("scrollLeftButton")->isVisible());
    QVERIFY(!button("scrollRightButton")->isVisible());
}

void TestTabStripWidths::newTabButtonFollowsTheLastTab()
{
    addTabs(3);
    QCOMPARE(view()->property("contentWidth").toReal(), 3 * 240.0);
    QCOMPARE(tabBar()->width(), 3 * 240.0);
    QCOMPARE(button("newTabButton")->x(), tabBar()->x() + tabBar()->width() + 2);
}

void TestTabStripWidths::tabsShrinkTogether()
{
    addTabs(7);
    const qreal expected = qFloor(m_strip->property("tabsAreaWidth").toReal() / 7);
    QVERIFY(expected < 240.0);
    QVERIFY(expected >= 120.0);
    QCOMPARE(tabWidth(), expected);
    QVERIFY(!m_strip->property("overflowing").toBool());
    for (int i = 0; i < 7; ++i)
        QCOMPARE(itemAt(i)->width(), expected);
}

void TestTabStripWidths::titleDoesNotChangeTheWidth()
{
    addTabs(3);
    m_tabs->currentTab()->setTitle(QString(200, QLatin1Char('x')));
    QTest::qWait(50);
    QCOMPARE(tabWidth(), 240.0);
    for (int i = 0; i < 3; ++i)
        QCOMPARE(itemAt(i)->width(), 240.0);
}

void TestTabStripWidths::manyTabsStopAtTheMinimumAndShowScrollButtons()
{
    addTabs(20);
    QCOMPARE(tabWidth(), 120.0);
    QVERIFY(m_strip->property("overflowing").toBool());
    QVERIFY(button("scrollLeftButton")->isVisible());
    QVERIFY(button("scrollRightButton")->isVisible());
    QCOMPARE(view()->property("contentWidth").toReal(), 20 * 120.0);
    QVERIFY(button("newTabButton")->x() + button("newTabButton")->width() <= m_strip->width());
}

void TestTabStripWidths::scrollButtonsAreDisabledAtTheEnds()
{
    addTabs(20);
    QTRY_VERIFY(!button("scrollRightButton")->isEnabled());
    QVERIFY(button("scrollLeftButton")->isEnabled());

    scrollTo(0);
    QTRY_VERIFY(!button("scrollLeftButton")->isEnabled());
    QVERIFY(button("scrollRightButton")->isEnabled());

    QQuickItem *right = button("scrollRightButton");
    QTest::mouseClick(m_window, Qt::LeftButton, {},
                      m_strip->mapToScene(right->boundingRect().center() + right->position()).toPoint());
    QTRY_COMPARE(scrolled(), 120.0);
    QVERIFY(button("scrollLeftButton")->isEnabled());
}

void TestTabStripWidths::verifyTabIsVisible(int index)
{
    QTRY_VERIFY(itemAt(index)->x() >= view()->property("contentX").toReal() - 0.5);
    QTRY_VERIFY(itemAt(index)->x() + itemAt(index)->width()
                <= view()->property("contentX").toReal() + view()->width() + 0.5);
}

void TestTabStripWidths::currentTabIsScrolledIntoView()
{
    addTabs(20);
    m_tabs->setCurrentIndex(0);
    QTRY_COMPARE(scrolled(), 0.0);

    m_tabs->setCurrentIndex(10);
    verifyTabIsVisible(10);

    resizeStrip(700);
    verifyTabIsVisible(10);
}

void TestTabStripWidths::pinnedTabsStayNarrow()
{
    addTabs(3);
    m_tabs->setPinned(0, true);
    QTest::qWait(50);
    QCOMPARE(itemAt(0)->width(), 36.0);
    QCOMPARE(itemAt(1)->width(), 240.0);
}

bool TestTabStripWidths::isInsideTabBar(int index) const
{
    QQuickItem *item = itemAt(index);
    const QRectF rect = tabBar()->mapRectFromItem(item, item->boundingRect());
    return rect.left() >= -0.5 && rect.right() <= tabBar()->width() + 0.5;
}

bool TestTabStripWidths::overlapsButton(int index, const char *buttonName) const
{
    QQuickItem *item = itemAt(index);
    QQuickItem *scrollButton = button(buttonName);
    const QRectF rect = m_strip->mapRectFromItem(item, item->boundingRect());
    const QRectF buttonRect(scrollButton->position(), scrollButton->size());
    return rect.intersects(buttonRect) && rect.intersected(buttonRect).width() > 0.5;
}

void TestTabStripWidths::scrolledOutTabsAreClipped()
{
    addTabs(20);
    QVERIFY(view()->property("clip").toBool());
}

void TestTabStripWidths::lastTabStaysClearOfTheRightButton()
{
    addTabs(20);
    m_tabs->setCurrentIndex(19);
    QTRY_VERIFY(!button("scrollRightButton")->isEnabled());
    QVERIFY(isInsideTabBar(19));
    QVERIFY(!overlapsButton(19, "scrollRightButton"));
    QVERIFY(button("scrollLeftButton")->isEnabled());
}

void TestTabStripWidths::firstTabStaysClearOfTheLeftButton()
{
    addTabs(20);
    m_tabs->setCurrentIndex(0);
    QTRY_VERIFY(!button("scrollLeftButton")->isEnabled());
    QVERIFY(isInsideTabBar(0));
    QVERIFY(!overlapsButton(0, "scrollLeftButton"));
    QVERIFY(button("scrollRightButton")->isEnabled());
}

int runTabStripWidths(int argc, char *argv[])
{
    TestTabStripWidths test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_tabstripwidths.moc"
