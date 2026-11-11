#include "notifier.h"

#include <QGuiApplication>

#ifdef Q_OS_WIN
#include <QIcon>
#include <QSystemTrayIcon>
#include <QTimer>
#else
#include <QDBusConnection>
#include <QDBusInterface>
#include <QStringList>
#include <QVariantMap>
#endif

namespace {
constexpr int kNotificationTimeoutMs = 5000;
}

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

#ifdef Q_OS_WIN
void Notifier::notify(const QString &title, const QString &body, const QString &iconName)
{
    Q_UNUSED(iconName)
    if (!QSystemTrayIcon::isSystemTrayAvailable())
        return;
    // One tray icon, shown only while notifications are recent.
    if (!m_trayIcon) {
        m_trayIcon = new QSystemTrayIcon(QIcon(QStringLiteral(":/packaging/kondor.png")), this);
        m_trayIcon->setToolTip(QGuiApplication::applicationDisplayName());
        m_hideTimer = new QTimer(this);
        m_hideTimer->setSingleShot(true);
        m_hideTimer->setInterval(10000);
        connect(m_hideTimer, &QTimer::timeout, m_trayIcon, &QSystemTrayIcon::hide);
    }
    m_trayIcon->show();
    m_trayIcon->showMessage(title, body,
                            QIcon(QStringLiteral(":/packaging/kondor.png")),
                            kNotificationTimeoutMs);
    m_hideTimer->start();
}
#else
void Notifier::notify(const QString &title, const QString &body, const QString &iconName)
{
    QDBusInterface notifications(QStringLiteral("org.freedesktop.Notifications"),
                                 QStringLiteral("/org/freedesktop/Notifications"),
                                 QStringLiteral("org.freedesktop.Notifications"),
                                 QDBusConnection::sessionBus());
    if (!notifications.isValid())
        return;

    // The Flatpak exports the application icon under its application ID.
    const QString appIcon = qEnvironmentVariable("FLATPAK_ID", QStringLiteral("kondor"));
    const QString icon = (iconName.isEmpty() || iconName == QLatin1String("kondor"))
        ? appIcon : iconName;
    notifications.call(QStringLiteral("Notify"),
                       QGuiApplication::applicationDisplayName(), // app_name
                       0u,                                        // replaces_id
                       icon,                      // app_icon
                       title,                     // summary
                       body,                      // body
                       QStringList(),             // actions
                       QVariantMap(),             // hints
                       kNotificationTimeoutMs);   // expire_timeout (ms)
}
#endif
