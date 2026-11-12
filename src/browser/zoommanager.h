#pragma once

#include <QObject>
#include <QSettings>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>

class QQmlEngine;
class QJSEngine;

// QML singleton `ZoomManager`: remembers the zoom factor per host in the
// `SiteZoom` group of ~/.config/KDE/Kondor.conf. Only factors other than 100%
// are stored. Private tabs only read it (callers must not call setZoomFor()
// for them).
class ZoomManager : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

public:
    static ZoomManager *instance();
    static ZoomManager *create(QQmlEngine *engine, QJSEngine *jsEngine);

    // The standard browser zoom levels.
    static QList<qreal> levels();

    // Host of an http(s) page URL; empty for anything else (no zoom memory).
    Q_INVOKABLE QString hostOf(const QUrl &url) const;
    // Saved factor for `host`, 1.0 when none.
    Q_INVOKABLE qreal zoomFor(const QString &host) const;
    Q_INVOKABLE void setZoomFor(const QString &host, qreal factor);
    // Next level above (direction > 0) or below (direction < 0) `current`,
    // clamped to the first/last level.
    Q_INVOKABLE qreal step(qreal current, int direction) const;

signals:
    void zoomChanged(const QString &host, qreal factor);

private:
    explicit ZoomManager(QObject *parent = nullptr);

    QSettings m_settings;
};
