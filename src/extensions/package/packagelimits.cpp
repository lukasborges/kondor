#include "extensions/package/packagelimits.h"

#include <QCoreApplication>
#include <QDirIterator>

#include "extensions/package/extensionpackage.h"

PackageSize measureDirectory(const QString &directory)
{
    PackageSize size;
    QDirIterator it(directory, QDir::Files | QDir::NoSymLinks, QDirIterator::Subdirectories);
    while (it.hasNext()) {
        it.next();
        size.bytes += it.fileInfo().size();
        ++size.files;
    }
    return size;
}

QString packageLimitError(const PackageSize &size)
{
    if (size.files > ExtensionPackage::kMaxPackageFiles)
        return QCoreApplication::translate("ExtensionPackage", "The package has more than %1 files")
            .arg(ExtensionPackage::kMaxPackageFiles);
    if (size.bytes > ExtensionPackage::kMaxPackageBytes)
        return QCoreApplication::translate("ExtensionPackage", "The package is larger than %1 MiB")
            .arg(ExtensionPackage::kMaxPackageBytes / (1024 * 1024));
    return QString();
}
