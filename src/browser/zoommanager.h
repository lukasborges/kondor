#pragma once

#include <QObject>
#include <QSettings>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>

class QQmlEngine;
class QJSEngine;

class ZoomManager : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

public:
    static ZoomManager *instance();
    static ZoomManager *create(QQmlEngine *engine, QJSEngine *jsEngine);

    static QList<qreal> levels();

    Q_INVOKABLE QString hostOf(const QUrl &url) const;
    Q_INVOKABLE qreal zoomFor(const QString &host) const;
    Q_INVOKABLE void setZoomFor(const QString &host, qreal factor);
    Q_INVOKABLE qreal step(qreal current, int direction) const;

signals:
    void zoomChanged(const QString &host, qreal factor);

private:
    explicit ZoomManager(QObject *parent = nullptr);

    void storeZoom(const QString &host, qreal factor);

    QSettings m_settings;
};
