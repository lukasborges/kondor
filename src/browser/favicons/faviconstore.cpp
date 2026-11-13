#include "browser/favicons/faviconstore.h"

#include "core/database/sql.h"

#include <QBuffer>
#include <QDateTime>
#include <QQmlEngine>
#include <QQuickImageProvider>
#include <QQuickTextureFactory>

#include <memory>

namespace {
constexpr int kMaxIconSize = 32;

bool isWebPage(const QUrl &url)
{
    return url.scheme() == QLatin1String("http") || url.scheme() == QLatin1String("https");
}

QString providerIconId(const QUrl &iconSource)
{
    const QString prefix = QStringLiteral("image://favicon/");
    const QString source = iconSource.toString();
    return source.startsWith(prefix) ? source.mid(prefix.size()) : QString();
}

QImage scaledToIconSize(const QImage &image)
{
    if (image.width() <= kMaxIconSize && image.height() <= kMaxIconSize)
        return image;
    return image.scaled(kMaxIconSize, kMaxIconSize, Qt::KeepAspectRatio, Qt::SmoothTransformation);
}

std::optional<QByteArray> encodePng(const QImage &image)
{
    QByteArray bytes;
    QBuffer buffer(&bytes);
    if (!buffer.open(QIODevice::WriteOnly) || !image.save(&buffer, "PNG"))
        return std::nullopt;
    return bytes;
}

bool isStoredWithBytes(const QString &host, const QByteArray &bytes)
{
    auto query = Sql::run(QStringLiteral("SELECT image FROM favicons WHERE host = ?"), {host});
    return query && query->next() && query->value(0).toByteArray() == bytes;
}
}

FaviconStore *FaviconStore::instance()
{
    static FaviconStore *store = new FaviconStore;
    return store;
}

FaviconStore *FaviconStore::create(QQmlEngine *engine, QJSEngine *)
{
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

void FaviconStore::bumpRevisionIfRowsAffected(const std::optional<QSqlQuery> &query)
{
    if (query && query->numRowsAffected() > 0)
        bumpRevision();
}

QQuickImageResponse *FaviconStore::requestIcon(const QString &iconId) const
{
    auto *provider = dynamic_cast<QQuickAsyncImageProvider *>(
            m_engine->imageProvider(QStringLiteral("favicon")));
    if (!provider)
        return nullptr;
    return provider->requestImageResponse(iconId, QSize(kMaxIconSize, kMaxIconSize));
}

void FaviconStore::storeResponse(QQuickImageResponse *response, const QString &host)
{
    const std::unique_ptr<QQuickTextureFactory> factory(response->textureFactory());
    const QImage image = factory ? factory->image() : QImage();
    if (!image.isNull())
        storeImage(host, scaledToIconSize(image));
    response->deleteLater();
}

void FaviconStore::store(const QUrl &pageUrl, const QUrl &iconSource)
{
    const QString iconId = providerIconId(iconSource);
    if (!m_engine || !isWebPage(pageUrl) || iconId.isEmpty())
        return;
    QQuickImageResponse *response = requestIcon(iconId);
    if (!response)
        return;
    connect(response, &QQuickImageResponse::finished, response,
            [this, response, host = pageUrl.host()] { storeResponse(response, host); });
}

void FaviconStore::storeImage(const QString &host, const QImage &image)
{
    if (host.isEmpty() || image.isNull())
        return;
    const std::optional<QByteArray> bytes = encodePng(image);
    if (!bytes || isStoredWithBytes(host, *bytes))
        return;
    const QString statement = QStringLiteral(
            "INSERT OR REPLACE INTO favicons (host, image, updated_at) VALUES (?, ?, ?)");
    if (Sql::run(statement, {host, *bytes, QDateTime::currentMSecsSinceEpoch()}))
        bumpRevision();
}

void FaviconStore::clearAll()
{
    bumpRevisionIfRowsAffected(Sql::run(QStringLiteral("DELETE FROM favicons")));
}

void FaviconStore::clearSince(qint64 msecsSinceEpoch)
{
    bumpRevisionIfRowsAffected(
            Sql::run(QStringLiteral("DELETE FROM favicons WHERE updated_at >= ?"),
                     {msecsSinceEpoch}));
}

QImage FaviconStore::imageForHost(const QString &host) const
{
    if (host.isEmpty())
        return QImage();
    auto query = Sql::run(QStringLiteral("SELECT image FROM favicons WHERE host = ?"), {host});
    if (!query || !query->next())
        return QImage();
    QImage image;
    if (!image.loadFromData(query->value(0).toByteArray(), "PNG"))
        return QImage();
    return image;
}
