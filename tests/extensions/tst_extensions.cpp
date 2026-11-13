#include <QGuiApplication>
#include <QQuickStyle>
#include <QTemporaryDir>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "../common/isolatedhome.h"
#include "extensionsharness.h"

namespace {

using TestRunner = int (*)(int, char **);

int runAll(int argc, char *argv[])
{
    const TestRunner runners[] = {
        runTestExtensionPackage, runTestExtensionScripts, runTestExtensionInstall,
        runTestExtensionReplace, runTestExtensionBridge, runTestExtensionBridgeTabs,
        runTestExtensionCatalog, runTestExtensionUpdates, runTestExtensionsUi,
        runTestExtensionsPanel, runTestPinnedToolBar, runTestExtensionsReloadBar, runTestExtensionPins,
        runTestExtensionDialogs, runTestExtensionPages, runTestUserScriptPackage,
        runTestUserScriptUpdate, runTestUserScriptPages, runTestPasswordsUi,
    };
    int failures = 0;
    for (const TestRunner runner : runners)
        failures += runner(argc, argv) != 0 ? 1 : 0;
    return failures;
}

}

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();

    QTemporaryDir home;
    if (!useIsolatedHome(home))
        return 1;

    QGuiApplication app(argc, argv);
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));
    QCoreApplication::setOrganizationName(QStringLiteral("KDE-Test"));
    QCoreApplication::setApplicationName(QStringLiteral("Kondor-Extensions-Test"));

    registerExtensionTypes();
    return runAll(argc, argv);
}
