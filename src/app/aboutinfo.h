#pragma once

#include <QObject>
#include <QString>
#include <QtQmlIntegration/qqmlintegration.h>

class QQmlEngine;
class QJSEngine;

// Read-only information shown in the "About Kondor Browser" window.
class AboutInfo : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    Q_PROPERTY(QString version READ version CONSTANT)
    Q_PROPERTY(QString qtRuntimeVersion READ qtRuntimeVersion CONSTANT)
    Q_PROPERTY(QString qtBuildVersion READ qtBuildVersion CONSTANT)
    Q_PROPERTY(QString webEngineVersion READ webEngineVersion CONSTANT)
    Q_PROPERTY(QString chromiumVersion READ chromiumVersion CONSTANT)
    Q_PROPERTY(QString windowingSystem READ windowingSystem CONSTANT)
    Q_PROPERTY(QString operatingSystem READ operatingSystem CONSTANT)
    Q_PROPERTY(QString licenseText READ licenseText CONSTANT)

public:
    static AboutInfo *instance();
    static AboutInfo *create(QQmlEngine *engine, QJSEngine *jsEngine);

    QString version() const;
    QString qtRuntimeVersion() const;
    QString qtBuildVersion() const;
    QString webEngineVersion() const;
    QString chromiumVersion() const;
    QString windowingSystem() const;
    QString operatingSystem() const;
    QString licenseText() const;

private:
    explicit AboutInfo(QObject *parent = nullptr);

    QString m_licenseText;
};
