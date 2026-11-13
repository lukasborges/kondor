#pragma once

#include <QImage>
#include <QObject>
#include <QSqlQuery>
#include <QUrl>
#include <optional>
#include <QtQmlIntegration/qqmlintegration.h>

class QQmlEngine;
class QQuickImageResponse;
class QSqlQuery;
class QJSEngine;
class FaviconStore : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    Q_PROPERTY(int revision READ revision NOTIFY revisionChanged)

public:
    static FaviconStore *instance();
    static FaviconStore *create(QQmlEngine *engine, QJSEngine *jsEngine);

    int revision() const;
    Q_INVOKABLE void store(const QUrl &pageUrl, const QUrl &iconSource);
    void storeImage(const QString &host, const QImage &image);
    void clearAll();
    void clearSince(qint64 msecsSinceEpoch);
    QImage imageForHost(const QString &host) const;

signals:
    void revisionChanged();

private:
    explicit FaviconStore(QObject *parent = nullptr);

    void bumpRevision();
    void bumpRevisionIfRowsAffected(const std::optional<QSqlQuery> &query);
    QQuickImageResponse *requestIcon(const QString &iconId) const;
    void storeResponse(QQuickImageResponse *response, const QString &host);

    QQmlEngine *m_engine = nullptr;
    int m_revision = 0;
};
