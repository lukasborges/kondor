#include <QGuiApplication>
#include <QQmlComponent>
#include <QQmlContext>
#include <QQmlEngine>
#include <QQmlExpression>
#include <QQuickItem>
#include <QQuickStyle>
#include <QQuickWindow>
#include <QSettings>
#include <QTemporaryDir>
#include <QTest>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "extensions/extensioncatalog.h"
#include "extensions/extensionmanager.h"
#include "passwords/passwordstore.h"
#include "browser/profilemanager.h"
#include "core/settings.h"
#include "browser/tabmodel.h"

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
    void clickingSidebarSwitchesPages();
    void arrowKeysMoveBetweenPages();
    void searchFiltersPages();
    void walletUnavailableState();

private:
    QQuickWindow *createWindow();
    int visiblePageCount(QQuickWindow *window);
    QQuickItem *sidebarEntry(QQuickWindow *window, int index);
    QPoint entryCenter(QQuickItem *entry) const;
    void typeText(QQuickWindow *window, const QString &text);
    void verifyShownPage(QQuickWindow *window, int page, const QString &title);
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
    qmlRegisterSingletonType<ExtensionManager>("Kondor", 1, 0, "ExtensionManager",
                                               [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                   return ExtensionManager::instance();
                                               });
    qmlRegisterSingletonType<ExtensionCatalog>("Kondor", 1, 0, "ExtensionCatalog",
                                               [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                   return ExtensionCatalog::instance();
                                               });
    qmlRegisterSingletonType<PasswordStore>("Kondor", 1, 0, "PasswordStore",
                                            [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                return PasswordStore::instance();
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
    m_engine.addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));
    QQmlComponent component(&m_engine, QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR
                                                                         "/settings/SettingsWindow.qml")));
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

QQuickItem *TestSettingsWindow::sidebarEntry(QQuickWindow *window, int index)
{
    QQmlExpression expression(qmlContext(window), window,
                              QStringLiteral("pageList.itemAtIndex(%1)").arg(index));
    const QVariant value = expression.evaluate();
    if (expression.hasError())
        qWarning() << expression.error();
    return value.value<QQuickItem *>();
}

QPoint TestSettingsWindow::entryCenter(QQuickItem *entry) const
{
    return entry->mapToScene(QPointF(entry->width() / 2, entry->height() / 2)).toPoint();
}

void TestSettingsWindow::typeText(QQuickWindow *window, const QString &text)
{
    for (const QChar character : text)
        QTest::keyClick(window, character.toLatin1());
}

// The heading, the page stack and the sidebar must all point at `page`.
void TestSettingsWindow::verifyShownPage(QQuickWindow *window, int page, const QString &title)
{
    QCOMPARE(window->property("currentPage").toInt(), page);

    QObject *heading = window->findChild<QObject *>(QStringLiteral("pageHeading"));
    QVERIFY(heading);
    QCOMPARE(heading->property("text").toString(), title);

    QObject *stack = window->findChild<QObject *>(QStringLiteral("pageStack"));
    QVERIFY(stack);
    QCOMPARE(stack->property("currentIndex").toInt(), page);

    QObject *list = window->findChild<QObject *>(QStringLiteral("pageList"));
    QVERIFY(list);
    QCOMPARE(list->property("currentIndex").toInt(), page);
    for (int i = 0; i < 4; ++i) {
        QQuickItem *entry = sidebarEntry(window, i);
        QVERIFY(entry);
        QCOMPARE(entry->property("highlighted").toBool(), i == page);
    }
}

void TestSettingsWindow::clickingSidebarSwitchesPages()
{
    const QStringList titles{ QStringLiteral("General"), QStringLiteral("Search"),
                              QStringLiteral("Downloads"), QStringLiteral("Privacy") };
    QQuickWindow *window = createWindow();
    QVERIFY(window);
    QMetaObject::invokeMethod(window, "showWindow");
    QVERIFY(QTest::qWaitForWindowExposed(window));

    // General is shown and highlighted when the window opens.
    verifyShownPage(window, 0, titles[0]);

    // Click each sidebar entry with the real mouse-event path.
    for (int page = 0; page < titles.size(); ++page) {
        QQuickItem *entry = nullptr;
        QTRY_VERIFY((entry = sidebarEntry(window, page)));
        QTest::mouseClick(window, Qt::LeftButton, Qt::NoModifier, entryCenter(entry));
        QTRY_COMPARE(window->property("currentPage").toInt(), page);
        verifyShownPage(window, page, titles[page]);
    }

    // Closing and reopening keeps the shown page, its heading and the
    // highlighted entry in sync.
    QMetaObject::invokeMethod(window, "discardChanges");
    QMetaObject::invokeMethod(window, "showWindow");
    QVERIFY(QTest::qWaitForWindowExposed(window));
    verifyShownPage(window, 3, titles[3]);

    delete window;
}

void TestSettingsWindow::arrowKeysMoveBetweenPages()
{
    QQuickWindow *window = createWindow();
    QVERIFY(window);
    QMetaObject::invokeMethod(window, "showWindow");
    QVERIFY(QTest::qWaitForWindowExposed(window));

    verifyShownPage(window, 0, QStringLiteral("General"));

    QTest::keyClick(window, Qt::Key_Down);
    verifyShownPage(window, 1, QStringLiteral("Search"));
    QTest::keyClick(window, Qt::Key_Down);
    verifyShownPage(window, 2, QStringLiteral("Downloads"));
    QTest::keyClick(window, Qt::Key_Up);
    verifyShownPage(window, 1, QStringLiteral("Search"));

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
    QVERIFY(QTest::qWaitForWindowExposed(window));
    QCOMPARE(visiblePageCount(window), 7);

    QObject *search = findByClassName(window, QStringLiteral("SearchField"));
    QVERIFY(search);
    auto *searchItem = qobject_cast<QQuickItem *>(search);
    QVERIFY(searchItem);
    searchItem->forceActiveFocus();

    // Typing "cookies" lists only Privacy, which is shown and highlighted.
    typeText(window, QStringLiteral("cookies"));
    QTRY_COMPARE(visiblePageCount(window), 1);
    QCOMPARE(window->property("currentPage").toInt(), 3);
    QCOMPARE(window->findChild<QObject *>(QStringLiteral("pageHeading"))->property("text").toString(),
             QStringLiteral("Privacy"));
    QCOMPARE(window->findChild<QObject *>(QStringLiteral("pageStack"))->property("currentIndex").toInt(), 3);

    QQuickItem *privacy = nullptr;
    QTRY_VERIFY((privacy = sidebarEntry(window, 0)));
    QCOMPARE(privacy->property("text").toString(), QStringLiteral("Privacy"));
    QVERIFY(privacy->property("highlighted").toBool());
    QVERIFY(!sidebarEntry(window, 1));

    // "engine" filters down to Search, shown the same way.
    QTest::keyClick(window, Qt::Key_A, Qt::ControlModifier);
    QTest::keyClick(window, Qt::Key_Delete);
    typeText(window, QStringLiteral("engine"));
    QTRY_COMPARE(visiblePageCount(window), 1);
    QCOMPARE(window->property("currentPage").toInt(), 1);
    QCOMPARE(window->findChild<QObject *>(QStringLiteral("pageHeading"))->property("text").toString(),
             QStringLiteral("Search"));

    // "kwallet" finds the Passwords page.
    QTest::keyClick(window, Qt::Key_A, Qt::ControlModifier);
    QTest::keyClick(window, Qt::Key_Delete);
    typeText(window, QStringLiteral("kwallet"));
    QTRY_COMPARE(visiblePageCount(window), 1);
    QCOMPARE(window->property("currentPage").toInt(), 4);
    QCOMPARE(window->findChild<QObject *>(QStringLiteral("pageHeading"))->property("text").toString(),
             QStringLiteral("Passwords"));

    // Clearing the filter restores every entry and keeps the page selected.
    QTest::keyClick(window, Qt::Key_A, Qt::ControlModifier);
    QTest::keyClick(window, Qt::Key_Delete);
    QTRY_COMPARE(visiblePageCount(window), 7);
    verifyShownPage(window, 4, QStringLiteral("Passwords"));

    delete window;
}

void TestSettingsWindow::walletUnavailableState()
{
    // KONDOR_NO_KWALLET=1 (set by CTest): the Passwords page shows the
    // wallet-denied state and never reaches the real wallet.
    QVERIFY(qEnvironmentVariableIntValue("KONDOR_NO_KWALLET") != 0);
    QQuickWindow *window = createWindow();
    QVERIFY(window);
    QMetaObject::invokeMethod(window, "showWindow");
    QVERIFY(QTest::qWaitForWindowExposed(window));
    window->setProperty("currentPage", 4);
    QTRY_COMPARE(PasswordStore::instance()->state(), QStringLiteral("unavailable"));
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
