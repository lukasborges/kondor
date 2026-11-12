#include "app/faviconimageprovider.h"

#include "browser/faviconstore.h"

#include <QUrl>

FaviconImageProvider::FaviconImageProvider()
    : QQuickImageProvider(QQuickImageProvider::Image)
{
}

QImage FaviconImageProvider::requestImage(const QString &id, QSize *size,
                                          const QSize &requestedSize)
{
    Q_UNUSED(requestedSize)
    const QImage image = FaviconStore::instance()->imageForHost(QUrl(id).host());
    if (size && !image.isNull())
        *size = image.size();
    return image;
}
