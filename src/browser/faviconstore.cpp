#include "browser/faviconstore.h"

#include "core/database.h"

#include <QBuffer>
#include <QDateTime>
#include <QQmlEngine>
#include <QQuickImageProvider>
#include <QQuickTextureFactory>
#include <QSqlQuery>
#include <QVariant>

namespace {
// Favicons are kept small: the UI never shows them larger than 22 px.
constexpr int kMaxIconSize = 32;
}

FaviconStore *FaviconStore::instance()
{
    static FaviconStore *store = new FaviconStore;
    return store;
}

FaviconStore *FaviconStore::create(QQmlEngine *engine, QJSEngine *jsEngine)
{
    Q_UNUSED(jsEngine)
    FaviconStore *store = instance();
    store->m_engine = engine;
    return store;
}

FaviconStore::FaviconStore(QObject *parent)
    : QObject(parent)
{
}

int FaviconStore::revision() const
{
    return m_revision;
}

void FaviconStore::bumpRevision()
{
    ++m_revision;
    emit revisionChanged();
}

void FaviconStore::store(const QUrl &pageUrl, const QUrl &iconSource)
{
    if (!m_engine || pageUrl.isEmpty() || iconSource.isEmpty())
        return;
    const QString scheme = pageUrl.scheme();
    if (scheme != QLatin1String("http") && scheme != QLatin1String("https"))
        return;

    const QString source = iconSource.toString();
    const QString prefix = QStringLiteral("image://favicon/");
    if (!source.startsWith(prefix))
        return;
    const QString iconId = source.mid(prefix.size());
    if (iconId.isEmpty())
        return;

    auto *provider = dynamic_cast<QQuickAsyncImageProvider *>(
        m_engine->imageProvider(QStringLiteral("favicon")));
    if (!provider)
        return;

    QQuickImageResponse *response =
        provider->requestImageResponse(iconId, QSize(kMaxIconSize, kMaxIconSize));
    if (!response)
        return;

    const QString host = pageUrl.host();
    connect(response, &QQuickImageResponse::finished, response,
            [this, response, host]() {
        QQuickTextureFactory *factory = response->textureFactory();
        if (factory) {
            const QImage image = factory->image();
            if (!image.isNull()) {
                const QImage scaled = image.width() > kMaxIconSize
                        || image.height() > kMaxIconSize
                    ? image.scaled(kMaxIconSize, kMaxIconSize, Qt::KeepAspectRatio,
                                   Qt::SmoothTransformation)
                    : image;
                storeImage(host, scaled);
            }
            delete factory;
        }
        response->deleteLater();
    });
}

void FaviconStore::storeImage(const QString &host, const QImage &image)
{
    if (host.isEmpty() || image.isNull())
        return;
    Database *db = Database::instance();
    if (!db->isValid())
        return;

    QByteArray bytes;
    QBuffer buffer(&bytes);
    if (!buffer.open(QIODevice::WriteOnly) || !image.save(&buffer, "PNG"))
        return;

    QSqlQuery existing(db->handle());
    existing.prepare(QStringLiteral("SELECT image FROM favicons WHERE host = ?"));
    existing.addBindValue(host);
    if (existing.exec() && existing.next() && existing.value(0).toByteArray() == bytes)
        return;

    QSqlQuery insert(db->handle());
    insert.prepare(QStringLiteral(
        "INSERT OR REPLACE INTO favicons (host, image, updated_at) VALUES (?, ?, ?)"));
    insert.addBindValue(host);
    insert.addBindValue(bytes);
    insert.addBindValue(QDateTime::currentMSecsSinceEpoch());
    if (insert.exec())
        bumpRevision();
}

void FaviconStore::clearAll()
{
    Database *db = Database::instance();
    if (!db->isValid())
        return;
    QSqlQuery query(db->handle());
    if (query.exec(QStringLiteral("DELETE FROM favicons")) && query.numRowsAffected() > 0)
        bumpRevision();
}

void FaviconStore::clearSince(qint64 msecsSinceEpoch)
{
    Database *db = Database::instance();
    if (!db->isValid())
        return;
    QSqlQuery query(db->handle());
    query.prepare(QStringLiteral("DELETE FROM favicons WHERE updated_at >= ?"));
    query.addBindValue(msecsSinceEpoch);
    if (query.exec() && query.numRowsAffected() > 0)
        bumpRevision();
}

QImage FaviconStore::imageForHost(const QString &host) const
{
    Database *db = Database::instance();
    if (host.isEmpty() || !db->isValid())
        return QImage();

    QSqlQuery query(db->handle());
    query.prepare(QStringLiteral("SELECT image FROM favicons WHERE host = ?"));
    query.addBindValue(host);
    if (!query.exec() || !query.next())
        return QImage();

    QImage image;
    if (!image.loadFromData(query.value(0).toByteArray(), "PNG"))
        return QImage();
    return image;
}
