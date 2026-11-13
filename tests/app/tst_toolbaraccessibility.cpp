#include <QGuiApplication>
#include <QQuickStyle>
#include <QTemporaryDir>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "adblock/adblockmanager.h"
#include "browser/searchsuggestions.h"
#include "common/accessibilitywalk.h"
#include "common/isolatedhome.h"
#include "downloads/downloadmanager.h"
#include "mainmenuharness.h"

class TestToolBarAccessibility : public MainMenuFixture
{
    Q_OBJECT

private slots:
    void initTestCase()
    {
        registerMenuTypes();
        registerToolBarTypes();
        QAccessible::setActive(true);
    }
    void everyVisibleToolBarButtonHasAName();

private:
    void registerToolBarTypes()
    {
        qmlRegisterUncreatableType<Tab>("Kondor", 1, 0, "Tab", QStringLiteral("Created by TabModel"));
        registerSingleton<SearchSuggestions>("SearchSuggestions");
        registerSingleton<AdBlockManager>("AdBlockManager");
        registerSingleton<DownloadManager>("DownloadManager");
        qmlRegisterSingletonType(QUrl::fromLocalFile(QStringLiteral(KONDOR_TEST_DATA_DIR
                                                                    "/ExtensionManagerStub.qml")),
                                 "Kondor", 1, 0, "ExtensionManager");
    }

    QByteArray toolBarWindow() const
    {
        const QByteArray stubWindow(kStubWindow);
        const QByteArray mainMenu("MainMenu {\n        id: mainMenu\n        browserWindow: window\n    }");
        const QByteArray toolBar("function openExtensionsSettings() {}\n"
                                 "    NavigationToolBar { tabs: tabs; browserWindow: window; width: 600 }");
        return QByteArray(stubWindow).replace(mainMenu, toolBar);
    }
};

void TestToolBarAccessibility::everyVisibleToolBarButtonHasAName()
{
    m_engine.addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));
    QQmlComponent component(&m_engine);
    component.setData(toolBarWindow(), QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR "/ToolBarWindow.qml")));
    auto *window = qobject_cast<QQuickWindow *>(component.create());
    QVERIFY2(window, qPrintable(component.errorString()));
    window->property("tabModel").value<TabModel *>()->addTab(false, QUrl(QStringLiteral("https://a.example")));
    QVERIFY(QTest::qWaitForWindowExposed(window));
    QCOMPARE(unnamedButtons(window->contentItem()), QStringList());
    delete window;
}

int main(int argc, char *argv[])
{
    QtWebEngineQuick::initialize();
    QTemporaryDir home;
    if (!useIsolatedHome(home))
        return 1;

    QGuiApplication app(argc, argv);
    QCoreApplication::setOrganizationName(QStringLiteral("KDE-Test"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor-ToolBar-Test"));
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));

    TestToolBarAccessibility test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_toolbaraccessibility.moc"
