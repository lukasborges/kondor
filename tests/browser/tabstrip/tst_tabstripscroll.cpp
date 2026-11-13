#include <QGuiApplication>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickItem>
#include <QQuickStyle>
#include <QQuickWindow>
#include <QTemporaryDir>
#include <QTest>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "browser/profile/profilemanager.h"
#include "browser/tabs/tab.h"
#include "browser/tabs/tabmodel.h"
#include "core/settings/settings.h"

class TestTabStripScroll : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void init();
    void cleanup();
    void newCurrentTabIsScrolledIntoView();
    void emptyAreaIsOnlyOutsideTabsAndButtons();

private:
    void addTabs(int count);
    QQuickItem *itemAt(int index) const;
    QQuickItem *tabBar() const { return m_strip->property("tabBar").value<QQuickItem *>(); }
    QQuickItem *view() const { return tabBar()->property("contentItem").value<QQuickItem *>(); }
    bool emptyAt(const QPointF &scenePoint) const;

    QQmlEngine m_engine;
    QQuickWindow *m_window = nullptr;
    QQuickItem *m_strip = nullptr;
    TabModel *m_tabs = nullptr;
};

void TestTabStripScroll::initTestCase()
{
    qmlRegisterType<TabModel>("Kondor", 1, 0, "TabModel");
    qmlRegisterUncreatableType<Tab>("Kondor", 1, 0, "Tab", QStringLiteral("Created by TabModel"));
    qmlRegisterSingletonType<ProfileManager>("Kondor", 1, 0, "ProfileManager",
        [](QQmlEngine *, QJSEngine *) -> QObject * { return ProfileManager::instance(); });
    qmlRegisterSingletonType<Settings>("Kondor", 1, 0, "Settings",
        [](QQmlEngine *, QJSEngine *) -> QObject * { return Settings::instance(); });
}

void TestTabStripScroll::init()
{
    m_tabs = new TabModel;
    m_window = new QQuickWindow;
    m_window->resize(1100, 60);
    m_engine.addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));
    QQmlComponent component(&m_engine, QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR "/browser/tabstrip/TabStrip.qml")));
    m_strip = qobject_cast<QQuickItem *>(component.createWithInitialProperties(
        { { QStringLiteral("tabModel"), QVariant::fromValue(m_tabs) } }));
    QVERIFY2(m_strip, qPrintable(component.errorString()));
    m_strip->setParentItem(m_window->contentItem());
    m_strip->setSize(QSizeF(1100, 36));
    m_window->show();
    QTest::mouseMove(m_window, QPoint(500, 58));
}

void TestTabStripScroll::cleanup()
{
    delete m_strip;
    delete m_window;
    delete m_tabs;
    m_strip = nullptr;
    m_window = nullptr;
    m_tabs = nullptr;
}

void TestTabStripScroll::addTabs(int count)
{
    for (int i = 0; i < count; ++i)
        m_tabs->addTab();
    QTest::qWait(50);
}

QQuickItem *TestTabStripScroll::itemAt(int index) const
{
    QQuickItem *item = nullptr;
    QMetaObject::invokeMethod(tabBar(), "itemAt", Q_RETURN_ARG(QQuickItem *, item), Q_ARG(int, index));
    return item;
}

bool TestTabStripScroll::emptyAt(const QPointF &scenePoint) const
{
    QVariant result;
    QMetaObject::invokeMethod(m_strip, "emptyAt", Q_RETURN_ARG(QVariant, result),
                              Q_ARG(QVariant, scenePoint.x()), Q_ARG(QVariant, scenePoint.y()));
    return result.toBool();
}

void TestTabStripScroll::newCurrentTabIsScrolledIntoView()
{
    addTabs(20);
    const qreal contentX = view()->property("contentX").toReal();
    QVERIFY(contentX > 0);
    QTRY_VERIFY(itemAt(19)->x() + itemAt(19)->width() <= view()->property("contentX").toReal() + view()->width() + 0.5);
    QVERIFY(itemAt(19)->x() >= view()->property("contentX").toReal() - 0.5);
}

void TestTabStripScroll::emptyAreaIsOnlyOutsideTabsAndButtons()
{
    addTabs(3);
    QQuickItem *newTab = m_strip->property("newTabButton").value<QQuickItem *>();
    const QPointF onTab = m_strip->mapToScene(QPointF(100, 18));
    const QPointF onButton = newTab->mapToScene(newTab->boundingRect().center());
    QVERIFY(!emptyAt(onTab));
    QVERIFY(!emptyAt(onButton));
    QVERIFY(emptyAt(m_strip->mapToScene(QPointF(1000, 18))));
}

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();
    QTemporaryDir home;
    if (!home.isValid())
        return 1;
    qputenv("XDG_DATA_HOME", home.path().toUtf8());
    qputenv("XDG_CONFIG_HOME", home.path().toUtf8());
    qputenv("XDG_CACHE_HOME", home.path().toUtf8());
    QGuiApplication app(argc, argv);
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));
    TestTabStripScroll test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_tabstripscroll.moc"
