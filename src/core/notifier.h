#pragma once

#include <QObject>
#include <QString>
#include <QtQmlIntegration/qqmlintegration.h>

class QQmlEngine;
class QJSEngine;

class Notifier : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

public:
    static Notifier *instance();
    static Notifier *create(QQmlEngine *engine, QJSEngine *jsEngine);

    Q_INVOKABLE void notify(const QString &title, const QString &body, const QString &iconName);

private:
    explicit Notifier(QObject *parent = nullptr);
};
