#include "notifier.h"

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

void Notifier::notify(const QString &title, const QString &body, const QString &iconName)
{
    QDBusInterface notifications(QStringLiteral("org.freedesktop.Notifications"),
                                 QStringLiteral("/org/freedesktop/Notifications"),
                                 QStringLiteral("org.freedesktop.Notifications"),
                                 QDBusConnection::sessionBus());
    if (!notifications.isValid())
        return;

    const QString icon = iconName.isEmpty() ? QStringLiteral("kondor") : iconName;
    notifications.call(QStringLiteral("Notify"),
                       QGuiApplication::applicationDisplayName(), // app_name
                       0u,                                        // replaces_id
                       icon,                      // app_icon
                       title,                     // summary
                       body,                      // body
                       QStringList(),             // actions
                       QVariantMap(),             // hints
                       5000);                     // expire_timeout (ms)
}
