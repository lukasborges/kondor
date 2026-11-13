#include "extensions/manifest/manifesticon.h"

#include <QDir>
#include <QImage>
#include <QUrl>

#include "extensions/package/packagepath.h"

namespace {

constexpr int kMinimumPngSize = 64;

bool endsWithIgnoringCase(const QString &icon, const char *suffix)
{
    return icon.endsWith(QLatin1String(suffix), Qt::CaseInsensitive);
}

bool isImageFile(const QString &icon)
{
    return endsWithIgnoringCase(icon, ".svg") || endsWithIgnoringCase(icon, ".png");
}

bool isTooSmall(const QImage &image)
{
    return image.isNull() || image.width() < kMinimumPngSize || image.height() < kMinimumPngSize;
}

QString imageError(const QString &directory, const QString &icon)
{
    const QString error = packageFileError(directory, icon, QStringLiteral("icon"));
    if (!error.isEmpty() || !endsWithIgnoringCase(icon, ".png"))
        return error;
    if (!isTooSmall(QImage(QDir(directory).filePath(icon))))
        return QString();
    return QStringLiteral("manifest.json: icon: a PNG icon must be at least 64 px: %1").arg(icon);
}

}

std::optional<QString> resolveManifestIcon(const QString &directory, const QString &icon,
                                           QString &error)
{
    if (icon.isEmpty())
        return QStringLiteral("preferences-plugin");
    if (!isImageFile(icon))
        return icon;
    error = imageError(directory, icon);
    if (!error.isEmpty())
        return std::nullopt;
    return QUrl::fromLocalFile(QDir(directory).filePath(icon)).toString();
}
