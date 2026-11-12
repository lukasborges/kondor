#pragma once

#include <QList>
#include <QObject>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>

class QQmlEngine;
class QJSEngine;

// QML singleton `StartupArgs`: command-line values parsed before the QML engine
// loads. Read-only for QML.
class StartupArgs : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    Q_PROPERTY(QList<QUrl> startupUrls READ startupUrls CONSTANT)
    Q_PROPERTY(bool startupPrivate READ startupPrivate CONSTANT)

public:
    static StartupArgs *instance();
    static StartupArgs *create(QQmlEngine *engine, QJSEngine *jsEngine);

    void setStartupUrls(const QList<QUrl> &urls) { m_startupUrls = urls; }
    void setStartupPrivate(bool isPrivate) { m_startupPrivate = isPrivate; }

    QList<QUrl> startupUrls() const { return m_startupUrls; }
    bool startupPrivate() const { return m_startupPrivate; }

private:
    explicit StartupArgs(QObject *parent = nullptr)
        : QObject(parent)
    {
    }

    QList<QUrl> m_startupUrls;
    bool m_startupPrivate = false;
};
