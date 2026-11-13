#include "extensions/package/packagepath.h"

#include <QDir>
#include <QFileInfo>
#include <QStringList>

#include <algorithm>

namespace {

bool hasForbiddenCharacter(const QString &path)
{
    return path.startsWith(QLatin1Char('/')) || path.contains(QLatin1Char('\\'))
        || QDir::isAbsolutePath(path) || path.contains(QLatin1Char(':'));
}

bool isUnsafePart(const QString &part)
{
    return part.isEmpty() || part == QLatin1String("..");
}

}

bool isSafeRelativePath(const QString &path)
{
    if (path.isEmpty() || hasForbiddenCharacter(path))
        return false;
    const QStringList parts = path.split(QLatin1Char('/'));
    return std::none_of(parts.begin(), parts.end(), isUnsafePart);
}

QString packageFileError(const QString &directory, const QString &path, const QString &where)
{
    if (!isSafeRelativePath(path))
        return QStringLiteral("manifest.json: %1: invalid path: %2").arg(where, path);
    const QFileInfo info(QDir(directory).filePath(path));
    if (!info.isFile() || info.isSymLink())
        return QStringLiteral("manifest.json: %1: file not found: %2").arg(where, path);
    return QString();
}
