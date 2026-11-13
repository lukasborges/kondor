#include "app/instance/windowactivation.h"

#include <QQuickWindow>

void raiseWindow(QObject *window, const QByteArray &activationToken)
{
    auto *quickWindow = qobject_cast<QQuickWindow *>(window);
    if (!quickWindow)
        return;
    if (!activationToken.isEmpty())
        qputenv("XDG_ACTIVATION_TOKEN", activationToken);
    quickWindow->raise();
    quickWindow->requestActivate();
}
