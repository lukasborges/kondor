#pragma once

#include <QImage>
#include <QObject>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>

class QQmlEngine;
class QJSEngine;

// QML singleton `FaviconStore`: keeps one favicon per host in the `favicons`
// table, filled only by normal tabs and shown through `image://kondor-favicon/`.
// Qt WebEngine's own `image://favicon/` provider only resolves icon URLs of
// open views, so Kondor cannot look up a page URL there.
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

    // `iconSource` is the tab's WebEngineView.icon (`image://favicon/<icon URL>`).
    // Ignored for empty values and non-http(s) page URLs. The image is fetched
    // from WebEngine's own provider and stored with storeImage().
    Q_INVOKABLE void store(const QUrl &pageUrl, const QUrl &iconSource);

    // The part that works without a WebEngine view (and what tests exercise):
    // encode the image as PNG and replace the row for `host`.
    void storeImage(const QString &host, const QImage &image);

    // Stored favicons reveal visited sites, so clearing history clears them too.
    void clearAll();
    void clearSince(qint64 msecsSinceEpoch);

    // Synchronous lookup used by the `kondor-favicon` image provider.
    QImage imageForHost(const QString &host) const;

signals:
    void revisionChanged();

private:
    explicit FaviconStore(QObject *parent = nullptr);

    void bumpRevision();

    QQmlEngine *m_engine = nullptr;
    int m_revision = 0;
};
