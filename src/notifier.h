#pragma once

#include <QObject>
#include <QString>
#include <QtQmlIntegration/qqmlintegration.h>

class QQmlEngine;
class QSystemTrayIcon;
class QTimer;
class QJSEngine;

// QML singleton `Notifier`: sends desktop notifications through the freedesktop
// notification service (org.freedesktop.Notifications) over D-Bus; on Windows
// as a toast of a tray icon shown only around notifications. Other
// components (downloads, crash notices, ...) share this block.
class Notifier : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

public:
    static Notifier *instance();
    static Notifier *create(QQmlEngine *engine, QJSEngine *jsEngine);

    // `iconName` follows the Breeze icon naming; when empty the app icon is used.
    Q_INVOKABLE void notify(const QString &title, const QString &body, const QString &iconName);

private:
    explicit Notifier(QObject *parent = nullptr);

#ifdef Q_OS_WIN
    QSystemTrayIcon *m_trayIcon = nullptr;
    QTimer *m_hideTimer = nullptr;
#endif
};
