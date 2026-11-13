#include <QGuiApplication>
#include <QQuickStyle>
#include <QTemporaryDir>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "../common/isolatedhome.h"
#include "mainmenuharness.h"

class TestMainMenu : public MainMenuFixture
{
    Q_OBJECT

private slots:
    void initTestCase() { registerMenuTypes(); }
    void init()
    {
        openStubWindow();
        showStubWindow();
    }
    void cleanup()
    {
        delete m_window;
        m_window = nullptr;
    }
    void rowsAndOrder();
    void historySubmenuListsRecentlyClosedTabs();
    void shortcutsWorkWithTheMenuClosed();
    void actionsDoNotShareASequenceWithAShortcut();
};

void TestMainMenu::rowsAndOrder()
{
    const QStringList rows = rowsOf(QStringLiteral("mainMenu"));
    QCOMPARE(rows, expectedTopLevelRows());
    QCOMPARE(rows.count(QStringLiteral("-")), 5);
    QCOMPARE(withoutSeparators(rows).size(), 13);
    QCOMPARE(rowsOf(QStringLiteral("mainMenu.itemAt(14).subMenu")), expectedMoreToolsRows());
    QCOMPARE(rowsOf(QStringLiteral("mainMenu.itemAt(17).subMenu")), expectedHelpRows());
}

void TestMainMenu::historySubmenuListsRecentlyClosedTabs()
{
    const QString history = QStringLiteral("mainMenu.itemAt(6).subMenu");
    evaluate(history + QStringLiteral(".aboutToShow()"));
    QCOMPARE(rowsOf(history), QStringList({"Show All History", "Reopen Closed Tab"}));

    m_tabs->addTab(false, QUrl(QStringLiteral("https://b.example")));
    m_tabs->addTab(false, QUrl(QStringLiteral("https://c.example")));
    m_tabs->closeTab(1);
    m_tabs->closeTab(1);
    evaluate(history + QStringLiteral(".aboutToShow()"));
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

    for (const QString &warning : std::as_const(collectedWarnings()))
        QVERIFY2(!warning.contains(QStringLiteral("Ambiguous")), qPrintable(warning));
}

void TestMainMenu::actionsDoNotShareASequenceWithAShortcut()
{
    const QStringList actions = sequencesIn(QStringLiteral("BrowserActions.qml"),
        QStringLiteral(R"(shortcut: ("[^"]+"|StandardKey\.\w+))"));
    const QStringList shortcuts = sequencesIn(QStringLiteral("BrowserShortcuts.qml"),
        QStringLiteral(R"(Shortcut \{\s*sequences?: ([^\n]+))"));
    QVERIFY(actions.size() >= 10 && !shortcuts.isEmpty());
    for (const QString &sequence : actions) {
        for (const QString &shortcut : shortcuts) {
            QVERIFY2(!shortcut.contains(sequence), qPrintable(sequence
                + QStringLiteral(" is both an Action and a Shortcut (ambiguous shortcut)")));
        }
    }
}

int main(int argc, char *argv[])
{
    QtWebEngineQuick::initialize();
    QTemporaryDir home;
    if (!useIsolatedHome(home))
        return 1;

    QGuiApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("KDE-Test"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor-MainMenu-Test"));
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));

    TestMainMenu test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_mainmenu.moc"
