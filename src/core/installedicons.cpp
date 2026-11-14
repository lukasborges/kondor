#include "core/installedicons.h"

#include <QStandardPaths>

InstalledIcons *InstalledIcons::instance()
{
    static InstalledIcons *installedIcons = new InstalledIcons;
    return installedIcons;
}

InstalledIcons *InstalledIcons::create(QQmlEngine *engine, QJSEngine *jsEngine)
{
    Q_UNUSED(engine)
    Q_UNUSED(jsEngine)
    return instance();
}

InstalledIcons::InstalledIcons(QObject *parent)
    : QObject(parent)
{
}

bool InstalledIcons::isInstalled(const QString &iconName) const
{
    const QString relativePath = QStringLiteral("icons/hicolor/scalable/actions/") + iconName + QStringLiteral(".svg");
    return !QStandardPaths::locate(QStandardPaths::GenericDataLocation, relativePath).isEmpty();
}
