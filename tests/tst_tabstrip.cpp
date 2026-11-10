#include <QGuiApplication>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickItem>
#include <QQuickStyle>
#include <QQuickWindow>
#include <QTemporaryDir>
#include <QTest>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "profilemanager.h"
#include "settings.h"
#include "tab.h"
#include "tabmodel.h"

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
    void pinnedTabsStayInTheirSection();
    void shortMoveIsAClick();

private:
    // Tab 1's left edge in strip coordinates, and its translate.
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

    QQmlComponent component(&m_engine, QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR
                                                                         "/TabStrip.qml")));
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

void TestTabStrip::draggedTabFollowsThePointerAndReordersLive()
{
    addTabs(5);
    const QList<Tab *> before = order();
    QQuickItem *dragged = itemAt(1);
    const qreal startLeft = leftOf(1);
    // Far enough for the dragged tab's center to pass the center of tab 2.
    const int far = int(leftOf(2) - startLeft) + 20;
    const QPoint press(int(startLeft) + 100, 18);
    QTest::mousePress(m_window, Qt::LeftButton, {}, press);
    int dx = 0;
    for (; dx <= 40; dx += 10)
        QTest::mouseMove(m_window, press + QPoint(dx, 0));
    QTest::qWait(50);
    QVERIFY(qAbs(dragged->mapToItem(m_strip, QPointF(0, 0)).x() - (startLeft + 40)) <= 1.0);
    QCOMPARE(order(), before);

    // Past the center of tab 2: reordered before the release.
    for (; dx < far; dx += 10)
        QTest::mouseMove(m_window, press + QPoint(dx, 0));
    QTest::mouseMove(m_window, press + QPoint(far, 0));
    QTest::qWait(100);
    QCOMPARE(tabAt(1), before[2]);
    QCOMPARE(tabAt(2), before[1]);
    QVERIFY(qAbs(dragged->mapToItem(m_strip, QPointF(0, 0)).x() - (startLeft + far)) <= 1.0);

    QTest::mouseRelease(m_window, Qt::LeftButton, {}, press + QPoint(far, 0));
    QTRY_COMPARE(dragged->property("dragShift").toReal(), 0.0);
    QCOMPARE(tabAt(2), before[1]);
    QCOMPARE(tabAt(0), before[0]);
    QCOMPARE(tabAt(3), before[3]);
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

#include "tst_tabstrip.moc"
