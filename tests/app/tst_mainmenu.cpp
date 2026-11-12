#include <QFile>
#include <QGuiApplication>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQmlExpression>
#include <QQuickImageProvider>
#include <QQuickStyle>
#include <QQuickWindow>
#include <QRegularExpression>
#include <QTemporaryDir>
#include <QTest>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "bookmarkmanager.h"
#include "database.h"
#include "faviconstore.h"
#include "historymanager.h"
#include "profilemanager.h"
#include "settings.h"
#include "tab.h"
#include "tabmodel.h"

namespace {
QStringList g_warnings;
QtMessageHandler g_previousHandler = nullptr;

void collectWarnings(QtMsgType type, const QMessageLogContext &context, const QString &message)
{
    g_warnings << message;
    g_previousHandler(type, context, message);
}

class EmptyImageProvider : public QQuickImageProvider
{
public:
    EmptyImageProvider()
        : QQuickImageProvider(QQuickImageProvider::Image)
    {
    }
    QImage requestImage(const QString &, QSize *size, const QSize &) override
    {
        QImage image(1, 1, QImage::Format_ARGB32);
        image.fill(Qt::transparent);
        if (size)
            *size = image.size();
        return image;
    }
};

// Stands in for the BrowserWindow: the same Action names, texts and shortcuts
// the real window declares, counting what they trigger.
const char *kStubWindow = R"(
import QtQuick
import QtQuick.Controls
import Kondor

ApplicationWindow {
    id: window
    width: 600
    height: 400
    visible: true

    property alias tabModel: tabs
    property int newTabs: 0
    property int reopens: 0
    property var openedUrls: []
    property bool windowFullScreen: false
    function openUrl(url, background) { openedUrls.push(url.toString()) }
    function openBookmarkEditor() {}
    function openBookmarks() {}

    TabModel { id: tabs }

    readonly property Action newTabAction: Action {
        text: "New Tab"; shortcut: "Ctrl+T"; onTriggered: window.newTabs++
    }
    readonly property Action newPrivateTabAction: Action { text: "New Private Tab"; shortcut: "Ctrl+Shift+N" }
    readonly property Action newWindowAction: Action { text: "New Window"; shortcut: "Ctrl+N" }
    readonly property Action newPrivateWindowAction: Action { text: "New Private Window"; shortcut: "Ctrl+Shift+P" }
    readonly property Action historyAction: Action { text: "Show All History"; shortcut: "Ctrl+H" }
    readonly property Action reopenClosedTabAction: Action {
        text: "Reopen Closed Tab"; shortcut: "Ctrl+Shift+T"
        enabled: tabs.canReopenClosedTab
        onTriggered: { tabs.reopenClosedTab(); window.reopens++ }
    }
    readonly property Action findAction: Action { text: "Find in Page…"; shortcut: StandardKey.Find }
    readonly property Action printAction: Action { text: "Print…"; shortcut: StandardKey.Print }
    readonly property Action savePageAction: Action { text: "Save Page As…"; shortcut: StandardKey.Save }
    readonly property Action devToolsAction: Action { text: "Developer Tools"; shortcut: "F12" }
    readonly property Action saveAsPdfAction: Action { text: "Save as PDF…" }
    readonly property Action sitePermissionsAction: Action { text: "Site Permissions…" }
    readonly property Action settingsAction: Action { text: "Configure Kondor Browser…"; shortcut: "Ctrl+," }
    readonly property Action reportBugAction: Action { text: "Report a Bug…" }
    readonly property Action aboutAction: Action { text: "About Kondor Browser" }

    MainMenu {
        id: mainMenu
        browserWindow: window
    }
}
)";
}

// The main menu (#93): rows and order, shortcuts working with the menu
// closed, and the History submenu.
class TestMainMenu : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void init();
    void cleanup();
    void rowsAndOrder();
    void historySubmenuListsRecentlyClosedTabs();
    void shortcutsWorkWithTheMenuClosed();
    void actionsDoNotShareASequenceWithAShortcut();

private:
    QStringList rowsOf(const QString &menuExpression);
    QQmlEngine m_engine;
    QQuickWindow *m_window = nullptr;
    TabModel *m_tabs = nullptr;
};

void TestMainMenu::initTestCase()
{
    QVERIFY(Database::instance()->isValid());
    qmlRegisterType<TabModel>("Kondor", 1, 0, "TabModel");
    qmlRegisterSingletonType<BookmarkManager>("Kondor", 1, 0, "BookmarkManager",
                                              [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                  return BookmarkManager::instance();
                                              });
    qmlRegisterSingletonType<HistoryManager>("Kondor", 1, 0, "HistoryManager",
                                             [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                 return HistoryManager::instance();
                                             });
    qmlRegisterSingletonType<FaviconStore>("Kondor", 1, 0, "FaviconStore",
                                           [](QQmlEngine *, QJSEngine *) -> QObject * {
                                               return FaviconStore::instance();
                                           });
    m_engine.addImageProvider(QStringLiteral("kondor-favicon"), new EmptyImageProvider);
    qmlRegisterSingletonType<Settings>("Kondor", 1, 0, "Settings",
                                       [](QQmlEngine *, QJSEngine *) -> QObject * {
                                           return Settings::instance();
                                       });
    qmlRegisterSingletonType<ProfileManager>("Kondor", 1, 0, "ProfileManager",
                                             [](QQmlEngine *, QJSEngine *) -> QObject * {
                                                 return ProfileManager::instance();
                                             });
    g_previousHandler = qInstallMessageHandler(collectWarnings);
}

void TestMainMenu::init()
{
    g_warnings.clear();
    // The stub imports MainMenu.qml and its neighbours from the source tree.
    m_engine.addImportPath(QStringLiteral(KONDOR_QML_DIR));
    QQmlComponent component(&m_engine);
    component.setData(kStubWindow,
                      QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR "/StubWindow.qml")));
    QObject *object = component.create();
    if (!object)
        qWarning() << component.errors();
    m_window = qobject_cast<QQuickWindow *>(object);
    QVERIFY(m_window);
    m_tabs = m_window->property("tabModel").value<TabModel *>();
    QVERIFY(m_tabs);
    m_tabs->addTab(false, QUrl(QStringLiteral("https://a.example")));
    m_window->show();
    m_window->requestActivate();
    QVERIFY(QTest::qWaitForWindowActive(m_window));
}

void TestMainMenu::cleanup()
{
    delete m_window;
    m_window = nullptr;
}

QStringList TestMainMenu::rowsOf(const QString &menuExpression)
{
    // "-" for a separator, "[row]" for the custom zoom row.
    const QString script = QStringLiteral(
        "(function(menu) { const rows = [];"
        " for (let i = 0; i < menu.count; ++i) { const it = menu.itemAt(i);"
        "   const kind = it.toString();"
        "   if (kind.indexOf('MenuSeparator') >= 0) rows.push('-');"
        "   else if (typeof it.text === 'string') rows.push(it.text);"
        "   else rows.push('[row]'); }"
        " return rows.join('|') })(%1)").arg(menuExpression);
    QQmlExpression expression(qmlContext(m_window), m_window, script);
    const QVariant value = expression.evaluate();
    if (expression.hasError())
        qWarning() << expression.error();
    return value.toString().split(QLatin1Char('|'));
}

void TestMainMenu::rowsAndOrder()
{
    const QStringList expected = {
        "New Tab", "New Private Tab", "New Window", "New Private Window", "-",
        "Bookmarks", "History", "-",
        "Find in Page…", "Print…", "Save Page As…", "-",
        "[row]", "-",
        "More Tools", "-",
        "Configure Kondor Browser…", "Help",
    };
    QCOMPARE(rowsOf(QStringLiteral("mainMenu")), expected);
    QCOMPARE(rowsOf(QStringLiteral("mainMenu")).count(QStringLiteral("-")), 5);

    const QStringList topLevel = [&] {
        QStringList rows = rowsOf(QStringLiteral("mainMenu"));
        rows.removeAll(QStringLiteral("-"));
        return rows;
    }();
    QCOMPARE(topLevel.size(), 13);

    // Submenus are reached through their MenuItem.subMenu.
    QCOMPARE(rowsOf(QStringLiteral("mainMenu.itemAt(14).subMenu")),
             QStringList({"Developer Tools", "Save as PDF…", "Site Permissions…"}));
    QCOMPARE(rowsOf(QStringLiteral("mainMenu.itemAt(17).subMenu")),
             QStringList({"Report a Bug…", "-", "About Kondor Browser"}));
}

void TestMainMenu::historySubmenuListsRecentlyClosedTabs()
{
    // Nothing closed yet: only the two static commands.
    const QString history = QStringLiteral("mainMenu.itemAt(6).subMenu");
    QQmlExpression open(qmlContext(m_window), m_window, history + QStringLiteral(".aboutToShow()"));
    open.evaluate();
    QCOMPARE(rowsOf(history), QStringList({"Show All History", "Reopen Closed Tab"}));

    m_tabs->addTab(false, QUrl(QStringLiteral("https://b.example")));
    m_tabs->addTab(false, QUrl(QStringLiteral("https://c.example")));
    m_tabs->closeTab(1);
    m_tabs->closeTab(1);
    QQmlExpression reopen(qmlContext(m_window), m_window, history + QStringLiteral(".aboutToShow()"));
    reopen.evaluate();
    const QStringList rows = rowsOf(history);
    QCOMPARE(rows.mid(0, 5), QStringList({"Show All History", "Reopen Closed Tab", "-",
                                         "Recently Closed Tabs", "https://c.example"}));
    QCOMPARE(rows.value(5), QStringLiteral("https://b.example"));
}

void TestMainMenu::shortcutsWorkWithTheMenuClosed()
{
    QTest::keyClick(m_window, Qt::Key_T, Qt::ControlModifier);
    QCOMPARE(m_window->property("newTabs").toInt(), 1);

    m_tabs->addTab(false, QUrl(QStringLiteral("https://b.example")));
    m_tabs->closeTab(1);
    QVERIFY(m_tabs->canReopenClosedTab());
    QTest::keyClick(m_window, Qt::Key_T, Qt::ControlModifier | Qt::ShiftModifier);
    QCOMPARE(m_window->property("reopens").toInt(), 1);
    QCOMPARE(m_tabs->count(), 2);

    for (const QString &warning : std::as_const(g_warnings))
        QVERIFY2(!warning.contains(QStringLiteral("Ambiguous")), qPrintable(warning));
}

// The Actions of the main menu own their sequences: BrowserWindow.qml must not
// also declare a Shortcut for them, or Qt reports "Ambiguous shortcut".
void TestMainMenu::actionsDoNotShareASequenceWithAShortcut()
{
    QFile file(QStringLiteral(KONDOR_QML_DIR "/BrowserWindow.qml"));
    QVERIFY(file.open(QIODevice::ReadOnly));
    const QString source = QString::fromUtf8(file.readAll());

    QStringList actionSequences;
    QRegularExpression actionRe(QStringLiteral(R"(shortcut: ("[^"]+"|StandardKey\.\w+))"));
    for (const QRegularExpressionMatch &m : actionRe.globalMatch(source))
        actionSequences << m.captured(1);
    QVERIFY(actionSequences.size() >= 10);

    QStringList shortcutSequences;
    QRegularExpression shortcutRe(QStringLiteral(R"(Shortcut \{\s*sequences?: ([^\n]+))"));
    for (const QRegularExpressionMatch &m : shortcutRe.globalMatch(source))
        shortcutSequences << m.captured(1);

    for (const QString &sequence : std::as_const(actionSequences)) {
        for (const QString &shortcut : std::as_const(shortcutSequences)) {
            QVERIFY2(!shortcut.contains(sequence),
                     qPrintable(QStringLiteral("%1 is both an Action and a Shortcut").arg(sequence)));
        }
    }
}

int main(int argc, char *argv[])
{
    QtWebEngineQuick::initialize();
    QTemporaryDir home;
    if (!home.isValid())
        return 1;
    qputenv("XDG_DATA_HOME", home.path().toUtf8());
    qputenv("XDG_CONFIG_HOME", home.path().toUtf8());
    qputenv("XDG_CACHE_HOME", home.path().toUtf8());

    QGuiApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("KDE-Test"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor-MainMenu-Test"));
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));

    TestMainMenu test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_mainmenu.moc"
