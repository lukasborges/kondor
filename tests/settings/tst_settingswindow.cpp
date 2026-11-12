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

template<typename T>
void registerSingleton(const char *name)
{
    qmlRegisterSingletonType<T>("Kondor", 1, 0, name,
                                [](QQmlEngine *, QJSEngine *) -> QObject * { return T::instance(); });
}

class TestSettingsWindow : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void init();
    void pendingChangesAreDiscarded();
    void applyWritesAndDisablesApply();
    void okAppliesAndCloses();
    void everyPageDefaultsResetOnlyItsOptions_data();
    void everyPageDefaultsResetOnlyItsOptions();
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
    void searchFor(QQuickWindow *window, const QString &text);
    void verifyOnlyPageIsListed(QQuickWindow *window, int page, const QString &title);
    void verifyShownPage(QQuickWindow *window, int page, const QString &title);
    QQmlEngine m_engine;
};

void TestSettingsWindow::initTestCase()
{
    qmlRegisterType<TabModel>("Kondor", 1, 0, "TabModel");
    registerSingleton<ProfileManager>("ProfileManager");
    registerSingleton<Settings>("Settings");
    registerSingleton<ExtensionManager>("ExtensionManager");
    registerSingleton<ExtensionCatalog>("ExtensionCatalog");
    registerSingleton<PasswordStore>("PasswordStore");
}

void TestSettingsWindow::init()
{
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
    QObject *list = window->findChild<QObject *>(QStringLiteral("pageList"));
    return list ? list->property("count").toInt() : -1;
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

namespace {
const QList<QPair<QByteArray, QVariant>> &changedOptionPerPage()
{
    static const QList<QPair<QByteArray, QVariant>> options{
        { "homePage", QStringLiteral("https://kde.org") },
        { "searchEngine", QStringLiteral("google") },
        { "askWhereToSave", true },
        { "blockThirdPartyCookies", true },
        { "offerToSavePasswords", false },
        { "extensionsAutoUpdate", false },
        { "spellCheckEnabled", false },
    };
    return options;
}

void verifyOnlyPageReturnedToDefault(QObject *draft, int page)
{
    for (int i = 0; i < changedOptionPerPage().size(); ++i) {
        const auto &option = changedOptionPerPage().at(i);
        const QVariant defaultValue = Settings::instance()->defaultValue(QString::fromLatin1(option.first));
        QCOMPARE(draft->property(option.first.constData()), i == page ? defaultValue : option.second);
    }
}
}

void TestSettingsWindow::everyPageDefaultsResetOnlyItsOptions_data()
{
    QTest::addColumn<int>("page");
    const QStringList titles{ "general", "search", "downloads", "privacy", "passwords",
                              "extensions", "spelling" };
    for (int page = 0; page < titles.size(); ++page)
        QTest::newRow(qPrintable(titles.at(page))) << page;
}

void TestSettingsWindow::everyPageDefaultsResetOnlyItsOptions()
{
    QFETCH(int, page);
    QQuickWindow *window = createWindow();
    QVERIFY(window);
    QMetaObject::invokeMethod(window, "showWindow");
    QObject *draft = pendingOf(window);
    QVERIFY(draft);
    for (const auto &option : changedOptionPerPage())
        draft->setProperty(option.first.constData(), option.second);
    window->setProperty("currentPage", page);
    QCOMPARE(window->property("defaultsEnabled").toBool(), true);
    QMetaObject::invokeMethod(window, "restoreDefaults");
    verifyOnlyPageReturnedToDefault(draft, page);
    QCOMPARE(window->property("defaultsEnabled").toBool(), false);
    delete window;
}

QQuickItem *TestSettingsWindow::sidebarEntry(QQuickWindow *window, int index)
{
    QObject *list = window->findChild<QObject *>(QStringLiteral("pageList"));
    QQuickItem *entry = nullptr;
    QMetaObject::invokeMethod(list, "itemAtIndex", Q_RETURN_ARG(QQuickItem *, entry),
                              Q_ARG(int, index));
    return entry;
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

    verifyShownPage(window, 0, titles[0]);

    for (int page = 0; page < titles.size(); ++page) {
        QQuickItem *entry = nullptr;
        QTRY_VERIFY((entry = sidebarEntry(window, page)));
        QTest::mouseClick(window, Qt::LeftButton, Qt::NoModifier, entryCenter(entry));
        QTRY_COMPARE(window->property("currentPage").toInt(), page);
        verifyShownPage(window, page, titles[page]);
    }

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

    QTest::keyClick(window, Qt::Key_Escape);
    QVERIFY(!window->isVisible());

    delete window;
}

void TestSettingsWindow::searchFor(QQuickWindow *window, const QString &text)
{
    QTest::keyClick(window, Qt::Key_A, Qt::ControlModifier);
    QTest::keyClick(window, Qt::Key_Delete);
    typeText(window, text);
}

void TestSettingsWindow::verifyOnlyPageIsListed(QQuickWindow *window, int page, const QString &title)
{
    QTRY_COMPARE(visiblePageCount(window), 1);
    QCOMPARE(window->property("currentPage").toInt(), page);
    QCOMPARE(window->findChild<QObject *>(QStringLiteral("pageHeading"))->property("text").toString(), title);
}

void TestSettingsWindow::searchFiltersPages()
{
    QQuickWindow *window = createWindow();
    QVERIFY(window);
    QMetaObject::invokeMethod(window, "showWindow");
    QVERIFY(QTest::qWaitForWindowExposed(window));
    QCOMPARE(visiblePageCount(window), 7);
    auto *searchItem = qobject_cast<QQuickItem *>(findByClassName(window, QStringLiteral("SearchField")));
    QVERIFY(searchItem);
    searchItem->forceActiveFocus();
    searchFor(window, QStringLiteral("cookies"));
    verifyOnlyPageIsListed(window, 3, QStringLiteral("Privacy"));
    QCOMPARE(window->findChild<QObject *>(QStringLiteral("pageStack"))->property("currentIndex").toInt(), 3);
    QQuickItem *privacy = nullptr;
    QTRY_VERIFY((privacy = sidebarEntry(window, 0)));
    QCOMPARE(privacy->property("text").toString(), QStringLiteral("Privacy"));
    QVERIFY(privacy->property("highlighted").toBool());
    QVERIFY(!sidebarEntry(window, 1));
    searchFor(window, QStringLiteral("engine"));
    verifyOnlyPageIsListed(window, 1, QStringLiteral("Search"));
    searchFor(window, QStringLiteral("kwallet"));
    verifyOnlyPageIsListed(window, 4, QStringLiteral("Passwords"));
    searchFor(window, QString());
    QTRY_COMPARE(visiblePageCount(window), 7);
    verifyShownPage(window, 4, QStringLiteral("Passwords"));
    delete window;
}

void TestSettingsWindow::walletUnavailableState()
{
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
