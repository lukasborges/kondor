#pragma once

#include <QQuickImageProvider>

class FaviconImageProvider : public QQuickImageProvider
{
public:
    FaviconImageProvider();

    QImage requestImage(const QString &id, QSize *size, const QSize &requestedSize) override;
};
