#pragma once

#include <QObject>
#include <QString>
#include <QtQmlIntegration/qqmlintegration.h>

class QQmlEngine;
class QJSEngine;

class InstalledIcons : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

public:
    static InstalledIcons *instance();
    static InstalledIcons *create(QQmlEngine *engine, QJSEngine *jsEngine);

    Q_INVOKABLE bool isInstalled(const QString &iconName) const;

private:
    explicit InstalledIcons(QObject *parent = nullptr);
};
