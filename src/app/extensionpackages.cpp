#include "app/extensionpackages.h"

#include <algorithm>

#include "extensions/packagesuffix.h"

namespace {
bool isLocalPackage(const QUrl &url)
{
    return url.isLocalFile() && hasPackageSuffix(url.toLocalFile());
}

QStringList localPaths(const QList<QUrl> &urls)
{
    QStringList paths;
    for (const QUrl &url : urls)
        paths.append(url.toLocalFile());
    return paths;
}
}

QStringList takeExtensionPackages(QList<QUrl> &urls)
{
    const auto firstPage = std::stable_partition(
        urls.begin(), urls.end(), [](const QUrl &url) { return !isLocalPackage(url); });
    const QList<QUrl> packages(firstPage, urls.end());
    urls.erase(firstPage, urls.end());
    return localPaths(packages);
}
