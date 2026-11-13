#include <QGuiApplication>
#include <QQuickStyle>
#include <QTemporaryDir>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "../common/isolatedhome.h"
#include "settingswindowharness.h"

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();
    QTemporaryDir home;
    if (!useIsolatedHome(home))
        return 1;
    QGuiApplication app(argc, argv);
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));
    const int applyFailures = runTestSettingsApply(argc, argv);
    return applyFailures + runTestSettingsNavigation(argc, argv);
}
