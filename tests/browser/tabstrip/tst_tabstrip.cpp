#include <QGuiApplication>
#include <QQuickStyle>
#include <QTemporaryDir>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

#include "../../common/isolatedhome.h"
#include "tabstripharness.h"

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();

    QTemporaryDir home;
    if (!useIsolatedHome(home))
        return 1;

    QGuiApplication app(argc, argv);
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));

    int failures = 0;
    failures |= runTabStripWidths(argc, argv);
    failures |= runTabStripClosing(argc, argv);
    failures |= runTabDrag(argc, argv);
    failures |= runTabDragScroll(argc, argv);
    failures |= runTabDragRelease(argc, argv);
    failures |= runTabStripAccessibility(argc, argv);
    return failures;
}
