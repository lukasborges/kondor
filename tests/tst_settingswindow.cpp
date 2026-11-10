#include <QGuiApplication>
#include <QQmlComponent>
#include <QQmlContext>
#include <QQmlEngine>
#include <QQmlExpression>
#include <QQuickStyle>
#include <QQuickWindow>
#include <QSettings>
#include <QTemporaryDir>
#include <QTest>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "profilemanager.h"
#include "settings.h"
#include "tabmodel.h"

namespace {
// The `pending` object is the only QML object with these properties.
QObject *pendingOf(QObject *parent)
{
    for (QObject *child : parent->children()) {
        if (child->property("searchEngine").isValid())
            return child;
        if (QObject *found = pendingOf(child))
            return found;
    }
    return nullptr;
}

QObject *findByClassName(QObject *parent, const QString &className)
{
    for (QObject *child : parent->children()) {
        if (QString::fromLatin1(child->metaObject()->className()).contains(className))
            return child;
        if (QObject *found = findByClassName(child, className))
            return found;
    }
    return nullptr;
}
}

// Drives the Configure window through its pending state and button actions,
// as a user would: nothing is written to Settings before Apply or OK.
class TestSettingsWindow : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void init();
    void pendingChangesAreDiscarded();
    void applyWritesAndDisablesApply();
    void okAppliesAndCloses();
    void defaultsResetOnlyTheCurrentPage();
    void searchFiltersPages();
    void arrowKeysMoveBetweenPages();

private:
    QQuickWindow *createWindow();
    int visiblePageCount(QQuickWindow *window);
    QQmlEngine m_engine;
};

void TestSettingsWindow::initTestCase()
{
    qmlRegisterType<TabModel>("Kondor", 1, 0, "TabModel");
    qmlRegisterSingletonType<ProfileManager>("Kondor", 1, 0, "ProfileManager",
                                             [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                 return ProfileManager::instance();
                                             });
    qmlRegisterSingletonType<Settings>("Kondor", 1, 0, "Settings",
                                       [](QQmlEngine *, QJSEngine *) -> QObject * {
                                           return Settings::instance();
                                       });
}

void TestSettingsWindow::init()
{
    // Every test starts from the defaults.
    Settings *settings = Settings::instance();
    settings->setHomePage(QString());
    settings->setSearchEngine(QStringLiteral("duckduckgo"));
    settings->setCustomSearchUrl(QString());
    settings->setAskWhereToSave(false);
    settings->setStartupBehavior(QStringLiteral("homepage"));
    settings->setShowTopSites(true);
    settings->setClearDataOnExit(false);
    settings->setBlockThirdPartyCookies(false);
}

QQuickWindow *TestSettingsWindow::createWindow()
{
    QQmlComponent component(&m_engine, QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR
                                                                         "/SettingsWindow.qml")));
    auto *tabs = new TabModel;
    QObject *object = component.createWithInitialProperties(
        { { QStringLiteral("tabModel"), QVariant::fromValue(tabs) } });
    if (!object) {
        qWarning() << component.errors();
        delete tabs;
        return nullptr;
    }
    auto *window = qobject_cast<QQuickWindow *>(object);
    if (!window) {
        delete object;
        delete tabs;
        return nullptr;
    }
    window->resize(860, 600);
    return window;
}

int TestSettingsWindow::visiblePageCount(QQuickWindow *window)
{
    QQmlExpression expression(qmlContext(window), window,
                              QStringLiteral("visiblePages.length"));
    const int count = expression.evaluate().toInt();
    if (expression.hasError())
        qWarning() << expression.error();
    return count;
}

void TestSettingsWindow::pendingChangesAreDiscarded()
{
    QQuickWindow *window = createWindow();
    QVERIFY(window);
    QMetaObject::invokeMethod(window, "showWindow");
    QVERIFY(window->isVisible());

    QObject *pending = pendingOf(window);
    QVERIFY(pending);
    QCOMPARE(window->property("modified").toBool(), false);

    pending->setProperty("searchEngine", "google");
    QCOMPARE(window->property("modified").toBool(), true);
    QCOMPARE(Settings::instance()->searchEngine(), QStringLiteral("duckduckgo"));

    QMetaObject::invokeMethod(window, "discardChanges");
    QVERIFY(!window->isVisible());
    QCOMPARE(Settings::instance()->searchEngine(), QStringLiteral("duckduckgo"));

    // Reopening always starts from the current Settings.
    QMetaObject::invokeMethod(window, "showWindow");
    QCOMPARE(pending->property("searchEngine").toString(), QStringLiteral("duckduckgo"));
    QCOMPARE(window->property("modified").toBool(), false);

    delete window;
}

void TestSettingsWindow::applyWritesAndDisablesApply()
{
    QQuickWindow *window = createWindow();
    QVERIFY(window);
    QMetaObject::invokeMethod(window, "showWindow");
    QObject *pending = pendingOf(window);
    QVERIFY(pending);

    pending->setProperty("searchEngine", "google");
    QMetaObject::invokeMethod(window, "applyChanges");

    QCOMPARE(Settings::instance()->searchEngine(), QStringLiteral("google"));
    QCOMPARE(window->property("modified").toBool(), false);

    delete window;
}

void TestSettingsWindow::okAppliesAndCloses()
{
    QQuickWindow *window = createWindow();
    QVERIFY(window);
    QMetaObject::invokeMethod(window, "showWindow");
    QObject *pending = pendingOf(window);
    QVERIFY(pending);

    pending->setProperty("customSearchUrl", "https://example.com/?q=%1");
    QMetaObject::invokeMethod(window, "acceptAndClose");

    QVERIFY(!window->isVisible());
    QCOMPARE(Settings::instance()->customSearchUrl(),
             QStringLiteral("https://example.com/?q=%1"));

    delete window;
}

void TestSettingsWindow::defaultsResetOnlyTheCurrentPage()
{
    QQuickWindow *window = createWindow();
    QVERIFY(window);
    QMetaObject::invokeMethod(window, "showWindow");
    QObject *pending = pendingOf(window);
    QVERIFY(pending);

    // General: change an option of this page and one of another page.
    window->setProperty("currentPage", 0);
    pending->setProperty("homePage", "https://kde.org");
    pending->setProperty("blockThirdPartyCookies", true);
    QCOMPARE(window->property("defaultsEnabled").toBool(), true);

    QMetaObject::invokeMethod(window, "restoreDefaults");

    QCOMPARE(pending->property("homePage").toString(), QString());
    QCOMPARE(pending->property("blockThirdPartyCookies").toBool(), true);
    QCOMPARE(window->property("defaultsEnabled").toBool(), false);
    // Resetting is pending only: Settings still has the old values.
    QCOMPARE(Settings::instance()->homePage(), QString());

    delete window;
}

void TestSettingsWindow::arrowKeysMoveBetweenPages()
{
    QQuickWindow *window = createWindow();
    QVERIFY(window);
    QMetaObject::invokeMethod(window, "showWindow");
    QCOMPARE(window->property("currentPage").toInt(), 0);

    QTest::keyClick(window, Qt::Key_Down);
    QCOMPARE(window->property("currentPage").toInt(), 1);
    QTest::keyClick(window, Qt::Key_Down);
    QCOMPARE(window->property("currentPage").toInt(), 2);
    QTest::keyClick(window, Qt::Key_Up);
    QCOMPARE(window->property("currentPage").toInt(), 1);

    // Esc discards and closes.
    QTest::keyClick(window, Qt::Key_Escape);
    QVERIFY(!window->isVisible());

    delete window;
}

void TestSettingsWindow::searchFiltersPages()
{
    QQuickWindow *window = createWindow();
    QVERIFY(window);
    QMetaObject::invokeMethod(window, "showWindow");
    QCOMPARE(visiblePageCount(window), 4);

    QObject *search = findByClassName(window, QStringLiteral("SearchField"));
    QVERIFY(search);

    // "cookies" filters down to Privacy, which becomes the current page.
    search->setProperty("text", "cookies");
    QCOMPARE(visiblePageCount(window), 1);
    QCOMPARE(window->property("currentPage").toInt(), 3);

    // "engine" filters down to Search.
    search->setProperty("text", "engine");
    QCOMPARE(visiblePageCount(window), 1);
    QCOMPARE(window->property("currentPage").toInt(), 1);

    search->setProperty("text", "");
    QCOMPARE(visiblePageCount(window), 4);

    delete window;
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

    TestSettingsWindow test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_settingswindow.moc"
