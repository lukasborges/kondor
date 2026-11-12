#include <QGuiApplication>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickItem>
#include <QQuickStyle>
#include <QQuickWindow>
#include <QTemporaryDir>
#include <QTest>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "browser/profilemanager.h"
#include "core/settings.h"
#include "browser/tab.h"
#include "browser/tabmodel.h"

// Tab sizing of the tab strip (#83): fixed width, shrinking, scroll buttons.
class TestTabStrip : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void init();
    void cleanup();
    void fewTabsKeepTheStandardWidth();
    void tabsShrinkTogether();
    void titleDoesNotChangeTheWidth();
    void manyTabsStopAtTheMinimumAndShowScrollButtons();
    void scrollButtonsAreDisabledAtTheEnds();
    void currentTabIsScrolledIntoView();
    void closingWithTheMouseKeepsTheWidth();
    void pinnedTabsStayNarrow();
    void scrolledOutTabsAreClipped();
    void draggedTabFollowsThePointerAndReordersLive();
    void draggedTabIsClampedToTheStrip();
    void draggingInAScrolledStripGoesTheRightWay();
    void draggingToTheEdgeAutoScrolls();
    void pinnedTabsStayInTheirSection();
    void shortMoveIsAClick();
    void closingAfterAClickDoesNotCrash();
    void releaseAnimatesIntoTheSlot();
    void currentTabIsVisibleAfterARelease();
    void closingTheDraggedTabResetsTheDragState();

private:
    // Left edge of a tab in strip coordinates.
    qreal leftOf(int index) const
    {
        return itemAt(index)->mapToItem(m_strip, QPointF(0, 0)).x();
    }
    Tab *tabAt(int i) const
    {
        return m_tabs->data(m_tabs->index(i), TabModel::TabRole).value<Tab *>();
    }
    QList<Tab *> order() const
    {
        QList<Tab *> list;
        for (int i = 0; i < m_tabs->count(); ++i)
            list << tabAt(i);
        return list;
    }
    void addTabs(int count);
    void resizeStrip(int width);
    qreal tabWidth() const { return m_strip->property("tabWidth").toReal(); }
    QQuickItem *itemAt(int index) const
    {
        QQuickItem *item = nullptr;
        QMetaObject::invokeMethod(tabBar(), "itemAt", Q_RETURN_ARG(QQuickItem *, item),
                                  Q_ARG(int, index));
        return item;
    }
    QQuickItem *button(const char *name) const
    {
        return m_strip->property(name).value<QQuickItem *>();
    }
    qreal scrolled() const { return m_strip->property("scrolled").toReal(); }
    QQuickItem *tabBar() const { return m_strip->property("tabBar").value<QQuickItem *>(); }
    QQuickItem *view() const { return tabBar()->property("contentItem").value<QQuickItem *>(); }

    QQmlEngine m_engine;
    QQuickWindow *m_window = nullptr;
    QQuickItem *m_strip = nullptr;
    QObject *m_stubWindow = nullptr;
    TabModel *m_tabs = nullptr;
};

void TestTabStrip::initTestCase()
{
    qmlRegisterType<TabModel>("Kondor", 1, 0, "TabModel");
    qmlRegisterUncreatableType<Tab>("Kondor", 1, 0, "Tab", QStringLiteral("Created by TabModel"));
    qmlRegisterSingletonType<ProfileManager>("Kondor", 1, 0, "ProfileManager",
                                             [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                 return ProfileManager::instance();
                                             });
    qmlRegisterSingletonType<Settings>("Kondor", 1, 0, "Settings",
                                       [](QQmlEngine *, QJSEngine *) -> QObject * {
                                           return Settings::instance();
                                       });
}

void TestTabStrip::init()
{
    m_tabs = new TabModel;
    m_window = new QQuickWindow;
    m_window->resize(1100, 60);

    m_engine.addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));

    QQmlComponent component(&m_engine, QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR
                                                                         "/browser/TabStrip.qml")));
    QObject *object = component.createWithInitialProperties(
        { { QStringLiteral("tabModel"), QVariant::fromValue(m_tabs) } });
    if (!object)
        qWarning() << component.errors();
    m_strip = qobject_cast<QQuickItem *>(object);
    // Stands in for the BrowserWindow: only closing a tab is needed.
    QQmlComponent stub(&m_engine);
    stub.setData("import QtQml\nQtObject { property var model\n"
                 "function closeTabFor(t) { model.closeTabObject(t) } }",
                 QUrl());
    m_stubWindow = stub.create();
    QVERIFY(m_stubWindow);
    m_stubWindow->setProperty("model", QVariant::fromValue(m_tabs));
    m_strip->setProperty("targetWindow", QVariant::fromValue(m_stubWindow));
    QVERIFY(m_strip);
    m_strip->setParentItem(m_window->contentItem());
    m_strip->setPosition(QPointF(0, 0));
    resizeStrip(1100);
    m_window->show();
    // Keep the pointer outside the strip.
    QTest::mouseMove(m_window, QPoint(500, 58));
}

void TestTabStrip::cleanup()
{
    delete m_strip;
    delete m_stubWindow;
    delete m_window;
    delete m_tabs;
    m_strip = nullptr;
    m_stubWindow = nullptr;
    m_window = nullptr;
    m_tabs = nullptr;
}

void TestTabStrip::addTabs(int count)
{
    for (int i = 0; i < count; ++i)
        m_tabs->addTab();
    QTest::qWait(50);
}

void TestTabStrip::resizeStrip(int width)
{
    m_strip->setSize(QSizeF(width, 36));
    QTest::qWait(50);
}

void TestTabStrip::fewTabsKeepTheStandardWidth()
{
    addTabs(3);
    QCOMPARE(tabWidth(), 240.0);
    QVERIFY(!m_strip->property("overflowing").toBool());
    QVERIFY(!button("scrollLeftButton")->isVisible());
    QVERIFY(!button("scrollRightButton")->isVisible());

    // The strip is count x 240 wide and the New Tab button follows the last tab.
    QCOMPARE(view()->property("contentWidth").toReal(), 3 * 240.0);
    QCOMPARE(tabBar()->width(), 3 * 240.0);
    QCOMPARE(button("newTabButton")->x(), tabBar()->x() + tabBar()->width() + 2);
}

void TestTabStrip::tabsShrinkTogether()
{
    addTabs(7);
    // Every tab shrinks by the same amount: the area shared by 7 tabs.
    const qreal expected = qFloor(m_strip->property("tabsAreaWidth").toReal() / 7);
    QVERIFY(expected < 240.0);
    QVERIFY(expected >= 120.0);
    QCOMPARE(tabWidth(), expected);
    QVERIFY(!m_strip->property("overflowing").toBool());
    for (int i = 0; i < 7; ++i)
        QCOMPARE(itemAt(i)->width(), expected);
}

void TestTabStrip::titleDoesNotChangeTheWidth()
{
    addTabs(3);
    m_tabs->currentTab()->setTitle(QString(200, QLatin1Char('x')));
    QTest::qWait(50);
    QCOMPARE(tabWidth(), 240.0);
    for (int i = 0; i < 3; ++i)
        QCOMPARE(itemAt(i)->width(), 240.0);
}

void TestTabStrip::manyTabsStopAtTheMinimumAndShowScrollButtons()
{
    addTabs(20);
    QCOMPARE(tabWidth(), 120.0);
    QVERIFY(m_strip->property("overflowing").toBool());
    QVERIFY(button("scrollLeftButton")->isVisible());
    QVERIFY(button("scrollRightButton")->isVisible());
    QCOMPARE(view()->property("contentWidth").toReal(), 20 * 120.0);
    // The New Tab button stays inside the strip.
    QVERIFY(button("newTabButton")->x() + button("newTabButton")->width() <= m_strip->width());
}

void TestTabStrip::scrollButtonsAreDisabledAtTheEnds()
{
    addTabs(20);
    // The new tab is current, so the strip is at its right end.
    QTRY_VERIFY(!button("scrollRightButton")->isEnabled());
    QVERIFY(button("scrollLeftButton")->isEnabled());

    // Back to the start: the left button is disabled, the right one enabled.
    QMetaObject::invokeMethod(m_strip, "scrollTo", Q_ARG(QVariant, 0));
    QTRY_VERIFY(!button("scrollLeftButton")->isEnabled());
    QVERIFY(button("scrollRightButton")->isEnabled());

    // One click scrolls by one minimum tab width.
    QTest::mouseClick(m_window, Qt::LeftButton, {},
                      m_strip->mapToScene(button("scrollRightButton")->boundingRect().center()
                                          + button("scrollRightButton")->position()).toPoint());
    QTRY_COMPARE(scrolled(), 120.0);
    QVERIFY(button("scrollLeftButton")->isEnabled());
}

void TestTabStrip::currentTabIsScrolledIntoView()
{
    addTabs(20);
    m_tabs->setCurrentIndex(0);
    QTRY_COMPARE(scrolled(), 0.0);

    m_tabs->setCurrentIndex(10);
    QTRY_VERIFY(itemAt(10)->x() >= view()->property("contentX").toReal() - 0.5);
    QTRY_VERIFY(itemAt(10)->x() + itemAt(10)->width()
                <= view()->property("contentX").toReal() + view()->width() + 0.5);

    // A window resize keeps it visible too.
    resizeStrip(700);
    QTRY_VERIFY(itemAt(10)->x() >= view()->property("contentX").toReal() - 0.5);
    QTRY_VERIFY(itemAt(10)->x() + itemAt(10)->width()
                <= view()->property("contentX").toReal() + view()->width() + 0.5);
}

void TestTabStrip::closingWithTheMouseKeepsTheWidth()
{
    addTabs(7);
    const qreal shrunk = tabWidth();
    QVERIFY(shrunk < 240.0);

    QMetaObject::invokeMethod(m_strip, "closeWithMouse", Q_ARG(QVariant, QVariant::fromValue(m_tabs->currentTab())));
    QCOMPARE(m_tabs->count(), 6);
    QCOMPARE(tabWidth(), shrunk);

    // The keyboard (a close that is not from the mouse) recomputes at once.
    m_tabs->closeTab(0);
    QCOMPARE(m_tabs->count(), 5);
    QVERIFY(tabWidth() > shrunk);

    // While the pointer is over the strip the widths stay, even after a second...
    addTabs(2);
    const qreal again = tabWidth();
    QTest::mouseMove(m_window, QPoint(500, 10));
    QMetaObject::invokeMethod(m_strip, "closeWithMouse",
                              Q_ARG(QVariant, QVariant::fromValue(m_tabs->currentTab())));
    QTest::qWait(1200);
    QCOMPARE(tabWidth(), again);

    // ...and they are recomputed as soon as it leaves.
    QTest::mouseMove(m_window, QPoint(500, 58));
    QTRY_VERIFY(tabWidth() > again);
}

void TestTabStrip::pinnedTabsStayNarrow()
{
    addTabs(3);
    m_tabs->setPinned(0, true);
    QTest::qWait(50);
    QCOMPARE(itemAt(0)->width(), 36.0);
    QCOMPARE(itemAt(1)->width(), 240.0);
}

void TestTabStrip::scrolledOutTabsAreClipped()
{
    addTabs(20);
    QVERIFY(view()->property("clip").toBool());

    auto inside = [&](int index) {
        QQuickItem *item = itemAt(index);
        const QRectF r = tabBar()->mapRectFromItem(item, item->boundingRect());
        return r.left() >= -0.5 && r.right() <= tabBar()->width() + 0.5;
    };
    auto overlaps = [&](int index, const char *buttonName) {
        QQuickItem *item = itemAt(index);
        QQuickItem *b = button(buttonName);
        const QRectF r = m_strip->mapRectFromItem(item, item->boundingRect());
        const QRectF br(b->position(), b->size());
        return r.intersects(br) && r.intersected(br).width() > 0.5;
    };

    // Last tab: current after addTabs.
    m_tabs->setCurrentIndex(19);
    QTRY_VERIFY(!button("scrollRightButton")->isEnabled());
    QVERIFY(inside(19));
    QVERIFY(!overlaps(19, "scrollRightButton"));
    QVERIFY(button("scrollLeftButton")->isEnabled());

    // First tab.
    m_tabs->setCurrentIndex(0);
    QTRY_VERIFY(!button("scrollLeftButton")->isEnabled());
    QVERIFY(inside(0));
    QVERIFY(!overlaps(0, "scrollLeftButton"));
    QVERIFY(button("scrollRightButton")->isEnabled());
}

void TestTabStrip::draggedTabFollowsThePointerAndReordersLive()
{
    addTabs(5);
    const QList<Tab *> before = order();
    m_tabs->setCurrentIndex(4);
    QQuickItem *dragged = itemAt(1);
    const qreal startLeft = leftOf(1);
    const qreal width = tabWidth();
    const QPoint press(int(startLeft) + 100, 18);
    auto moveBy = [&](int dx) {
        const int step = dx < 0 ? -5 : 5;
        for (int d = step; qAbs(d) < qAbs(dx); d += step)
            QTest::mouseMove(m_window, press + QPoint(d, 0));
        QTest::mouseMove(m_window, press + QPoint(dx, 0));
        QTest::qWait(60);
    };
    auto left = [&] { return dragged->mapToItem(m_strip, QPointF(0, 0)).x(); };

    QTest::mousePress(m_window, Qt::LeftButton, {}, press);
    // The origin may be non-zero: the checks below must not depend on it.
    moveBy(int(width / 2) - 5);
    QVERIFY(qAbs(left() - (startLeft + int(width / 2) - 5)) <= 1.0);
    QCOMPARE(order(), before);
    // Starting the drag selects the dragged tab.
    QCOMPARE(m_tabs->currentTab(), before[1]);

    moveBy(int(width / 2) + 5);
    QCOMPARE(tabAt(1), before[2]);
    QCOMPARE(tabAt(2), before[1]);
    QVERIFY(qAbs(left() - (startLeft + int(width / 2) + 5)) <= 1.0);

    // Next swap: past the center of tab 3.
    moveBy(int(width * 1.5) - 5);
    QCOMPARE(tabAt(2), before[1]);
    moveBy(int(width * 1.5) + 5);
    QCOMPARE(tabAt(3), before[1]);
    QVERIFY(qAbs(left() - (startLeft + int(width * 1.5) + 5)) <= 1.0);

    QTest::mouseRelease(m_window, Qt::LeftButton, {}, press + QPoint(int(width * 1.5) + 5, 0));
    QTRY_COMPARE(dragged->property("dragShift").toReal(), 0.0);
    QCOMPARE(tabAt(3), before[1]);
    QCOMPARE(m_tabs->currentTab(), before[1]);
}

void TestTabStrip::draggedTabIsClampedToTheStrip()
{
    addTabs(5);
    const QList<Tab *> before = order();
    QQuickItem *dragged = itemAt(3);
    const qreal first = leftOf(0);
    const qreal last = leftOf(4);
    const QPoint press(int(leftOf(3)) + 100, 18);
    QTest::mousePress(m_window, Qt::LeftButton, {}, press);
    for (int dx = -10; press.x() + dx > 2; dx -= 10)
        QTest::mouseMove(m_window, press + QPoint(dx, 0));
    QTest::qWait(100);
    QCOMPARE(tabAt(0), before[3]);
    QVERIFY(qAbs(dragged->mapToItem(m_strip, QPointF(0, 0)).x() - first) <= 1.0);
    for (int dx = -press.x() + 5; dx <= 1090 - press.x(); dx += 20)
        QTest::mouseMove(m_window, press + QPoint(dx, 0));
    QTest::qWait(100);
    QCOMPARE(tabAt(4), before[3]);
    QVERIFY(qAbs(dragged->mapToItem(m_strip, QPointF(0, 0)).x() - last) <= 1.0);
    QTest::mouseRelease(m_window, Qt::LeftButton, {}, press + QPoint(1090 - press.x(), 0));
    QTRY_COMPARE(dragged->property("dragShift").toReal(), 0.0);
}

void TestTabStrip::draggingInAScrolledStripGoesTheRightWay()
{
    resizeStrip(1100);
    addTabs(30);
    const qreal maxScroll = m_strip->property("maxScroll").toReal();
    QVERIFY(maxScroll > 0);
    QMetaObject::invokeMethod(m_strip, "scrollTo", Q_ARG(QVariant, maxScroll));
    QTRY_COMPARE(scrolled(), maxScroll);
    const QList<Tab *> before = order();
    QQuickItem *dragged = itemAt(27);
    const qreal startLeft = leftOf(27);
    const QPoint press(int(startLeft) + 30, 18);
    QTest::mousePress(m_window, Qt::LeftButton, {}, press);
    for (int dx = -10; dx >= -130; dx -= 10)
        QTest::mouseMove(m_window, press + QPoint(dx, 0));
    QTest::qWait(100);
    QCOMPARE(tabAt(26), before[27]);
    QVERIFY(qAbs(dragged->mapToItem(m_strip, QPointF(0, 0)).x() - (startLeft - 130)) <= 1.0);
    QTest::mouseRelease(m_window, Qt::LeftButton, {}, press + QPoint(-130, 0));
    QTRY_COMPARE(dragged->property("dragShift").toReal(), 0.0);
}

void TestTabStrip::draggingToTheEdgeAutoScrolls()
{
    resizeStrip(1100);
    addTabs(30);
    QMetaObject::invokeMethod(m_strip, "scrollTo", Q_ARG(QVariant, 0.0));
    QTRY_COMPARE(scrolled(), 0.0);
    const qreal maxScroll = m_strip->property("maxScroll").toReal();
    const QList<Tab *> before = order();
    QQuickItem *dragged = itemAt(1);
    const QPoint press(int(leftOf(1)) + 30, 18);
    QTest::mousePress(m_window, Qt::LeftButton, {}, press);
    const int viewWidth = int(view()->width());
    for (int x = press.x(); x < viewWidth - 10; x += 20)
        QTest::mouseMove(m_window, QPoint(x, 18));
    const QPoint edge(viewWidth - 10, 18);
    QTest::mouseMove(m_window, edge);
    QTRY_VERIFY_WITH_TIMEOUT(scrolled() > 50, 2000);
    QTRY_COMPARE_WITH_TIMEOUT(scrolled(), maxScroll, 10000);
    QTRY_COMPARE(tabAt(29), before[1]);
    QVERIFY(qAbs(dragged->mapToItem(m_strip, QPointF(0, 0)).x() - leftOf(29)) <= 1.0);

    // Leaving the edge zone stops the scrolling.
    QTest::mouseMove(m_window, QPoint(viewWidth / 2, 18));
    QTest::qWait(100);
    const qreal stopped = scrolled();
    QTest::qWait(150);
    QCOMPARE(scrolled(), stopped);
    QTest::mouseRelease(m_window, Qt::LeftButton, {}, QPoint(viewWidth / 2, 18));
    QTRY_COMPARE(dragged->property("dragShift").toReal(), 0.0);
}

void TestTabStrip::pinnedTabsStayInTheirSection()
{
    addTabs(5);
    m_tabs->setPinned(0, true);
    m_tabs->setPinned(1, true);
    QTest::qWait(100);
    const QList<Tab *> before = order();
    const QPoint press(int(leftOf(0)) + 18, 18);
    QTest::mousePress(m_window, Qt::LeftButton, {}, press);
    for (int dx = 0; dx <= 400; dx += 20)
        QTest::mouseMove(m_window, press + QPoint(dx, 0));
    QTest::qWait(100);
    QCOMPARE(tabAt(1), before[0]);
    QCOMPARE(tabAt(2), before[2]);
    QTest::mouseRelease(m_window, Qt::LeftButton, {}, press + QPoint(400, 0));
    QTest::qWait(100);
    QVERIFY(tabAt(0)->pinned() && tabAt(1)->pinned());
}

void TestTabStrip::shortMoveIsAClick()
{
    addTabs(5);
    const QList<Tab *> before = order();
    const QPoint press(int(leftOf(1)) + 100, 18);
    QTest::mousePress(m_window, Qt::LeftButton, {}, press);
    QTest::mouseMove(m_window, press + QPoint(2, 0));
    QTest::mouseRelease(m_window, Qt::LeftButton, {}, press + QPoint(2, 0));
    QTest::qWait(50);
    QCOMPARE(order(), before);
    QCOMPARE(m_tabs->currentIndex(), 1);
}

void TestTabStrip::closingAfterAClickDoesNotCrash()
{
    // Regression: ListView move/displaced transitions crashed here.
    for (int variant = 0; variant < 4; ++variant) {
        cleanup();
        init();
        addTabs(5);
        m_tabs->setCurrentIndex(variant < 3 ? 4 : 1);
        QTest::mouseClick(m_window, Qt::LeftButton, {}, QPoint(int(leftOf(1)) + 60, 18));
        QTest::qWait(1000);
        if (variant == 0) {
            QTest::mouseClick(m_window, Qt::LeftButton, {},
                              QPoint(int(leftOf(1) + tabWidth()) - 14, 18));
        } else if (variant == 1) {
            QTest::mouseClick(m_window, Qt::LeftButton, {},
                              QPoint(int(leftOf(2) + tabWidth()) - 14, 18));
        } else {
            QTest::mouseClick(m_window, Qt::MiddleButton, {}, QPoint(int(leftOf(2)) + 60, 18));
        }
        QTest::qWait(300);
        QCOMPARE(m_tabs->count(), 4);
    }
}

void TestTabStrip::releaseAnimatesIntoTheSlot()
{
    addTabs(5);
    QQuickItem *dragged = itemAt(1);
    const QPoint press(int(leftOf(1)) + 100, 18);
    QTest::mousePress(m_window, Qt::LeftButton, {}, press);
    for (int dx = 5; dx <= 40; dx += 5)
        QTest::mouseMove(m_window, press + QPoint(dx, 0));
    QTest::qWait(60);
    QVERIFY(dragged->property("dragShift").toReal() != 0.0);
    QTest::mouseRelease(m_window, Qt::LeftButton, {}, press + QPoint(40, 0));
    QVERIFY(dragged->property("dragShift").toReal() != 0.0);
    QTRY_COMPARE(dragged->property("dragShift").toReal(), 0.0);
}

void TestTabStrip::currentTabIsVisibleAfterARelease()
{
    resizeStrip(1100);
    addTabs(30);
    QMetaObject::invokeMethod(m_strip, "scrollTo", Q_ARG(QVariant, 253.0));
    QTRY_COMPARE(scrolled(), 253.0);
    int index = 0;
    while (index < 29 && leftOf(index) < 40)
        ++index;
    const QPoint press(int(leftOf(index)) + int(tabWidth()) - 30, 18);
    QTest::mousePress(m_window, Qt::LeftButton, {}, press);
    for (int x = press.x(); x > 40; x -= 10)
        QTest::mouseMove(m_window, QPoint(x, 18));
    QTest::mouseMove(m_window, QPoint(40, 18));
    QTest::qWait(60);
    QTest::mouseRelease(m_window, Qt::LeftButton, {}, QPoint(40, 18));
    QQuickItem *current = itemAt(m_tabs->currentIndex());
    QTRY_VERIFY(current->mapToItem(view(), QPointF(0, 0)).x() >= -0.5
                && current->mapToItem(view(), QPointF(current->width(), 0)).x() <= view()->width() + 0.5);
}

void TestTabStrip::closingTheDraggedTabResetsTheDragState()
{
    addTabs(5);
    const QPoint press(int(leftOf(1)) + 100, 18);
    QTest::mousePress(m_window, Qt::LeftButton, {}, press);
    for (int dx = 5; dx <= 60; dx += 5)
        QTest::mouseMove(m_window, press + QPoint(dx, 0));
    QTest::qWait(60);
    QVERIFY(m_strip->property("tabDragActive").toBool());
    m_tabs->closeTabObject(tabAt(m_tabs->currentIndex()));
    QTest::mouseRelease(m_window, Qt::LeftButton, {}, press + QPoint(60, 0));
    QTest::qWait(300);
    QCOMPARE(m_strip->property("tabDragActive").toBool(), false);
    QCOMPARE(m_tabs->count(), 4);
}

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();

    // Never touch the real profile: settings live in the temporary home.
    QTemporaryDir home;
    if (!home.isValid())
        return 1;
    qputenv("XDG_DATA_HOME", home.path().toUtf8());
    qputenv("XDG_CONFIG_HOME", home.path().toUtf8());
    qputenv("XDG_CACHE_HOME", home.path().toUtf8());

    QGuiApplication app(argc, argv);
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));

    TestTabStrip test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_tabstrip.moc"
