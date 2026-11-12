#include "core/notifier.h"

#include <QDBusConnection>
#include <QDBusInterface>
#include <QGuiApplication>
#include <QStringList>
#include <QVariantMap>

Notifier *Notifier::instance()
{
    static Notifier *notifier = new Notifier;
    return notifier;
}

Notifier *Notifier::create(QQmlEngine *engine, QJSEngine *jsEngine)
{
    Q_UNUSED(engine)
    Q_UNUSED(jsEngine)
    return instance();
}

Notifier::Notifier(QObject *parent)
    : QObject(parent)
{
}

namespace {

QString applicationIcon(const QString &iconName)
{
    const QString appIcon = qEnvironmentVariable("FLATPAK_ID", QStringLiteral("kondor"));
    const bool usesAppIcon = iconName.isEmpty() || iconName == QLatin1String("kondor");
    return usesAppIcon ? appIcon : iconName;
}

QVariantList notifyArguments(const QString &title, const QString &body, const QString &icon)
{
    return {QGuiApplication::applicationDisplayName(), 0u, icon, title, body,
            QStringList(), QVariantMap(), 5000};
}

}

void Notifier::notify(const QString &title, const QString &body, const QString &iconName)
{
    QDBusInterface notifications(QStringLiteral("org.freedesktop.Notifications"),
                                 QStringLiteral("/org/freedesktop/Notifications"),
                                 QStringLiteral("org.freedesktop.Notifications"),
                                 QDBusConnection::sessionBus());
    if (!notifications.isValid())
        return;
    notifications.callWithArgumentList(QDBus::Block, QStringLiteral("Notify"),
                                       notifyArguments(title, body, applicationIcon(iconName)));
}
