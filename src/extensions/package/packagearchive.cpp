#include "extensions/package/extensionpackage.h"

#include <QCoreApplication>
#include <QDir>
#include <QFile>
#include <QFileInfo>

#include <KArchive>
#include <KZip>

#include "extensions/package/packagelimits.h"
#include "extensions/package/packagepath.h"

namespace {

struct ArchiveFile {
    QString path;
    const KArchiveFile *file;
};

struct ArchiveListing {
    QList<ArchiveFile> files;
    PackageSize size;
    QString error;
};

bool report(QString *error, const QString &message)
{
    if (error)
        *error = message;
    return false;
}

void listDirectory(const KArchiveDirectory *directory, const QString &prefix,
                   ArchiveListing &listing);

void addFile(const KArchiveFile *file, const QString &path, ArchiveListing &listing)
{
    if (!isSafeRelativePath(path)) {
        listing.error = QCoreApplication::translate("ExtensionPackage", "Unsafe file name in the package: %1").arg(path);
        return;
    }
    listing.size.bytes += file->size();
    ++listing.size.files;
    listing.files.append({path, file});
    listing.error = packageLimitError(listing.size);
}

void listEntry(const KArchiveEntry *entry, const QString &path, ArchiveListing &listing)
{
    if (entry->isDirectory())
        listDirectory(static_cast<const KArchiveDirectory *>(entry), path + QLatin1Char('/'), listing);
    else
        addFile(static_cast<const KArchiveFile *>(entry), path, listing);
}

void listDirectory(const KArchiveDirectory *directory, const QString &prefix,
                   ArchiveListing &listing)
{
    const QStringList names = directory->entries();
    for (const QString &name : names) {
        if (!listing.error.isEmpty())
            return;
        listEntry(directory->entry(name), prefix + name, listing);
    }
}

bool writeArchiveFile(const ArchiveFile &entry, const QDir &target)
{
    const QString destination = target.filePath(entry.path);
    QDir().mkpath(QFileInfo(destination).absolutePath());
    QFile out(destination);
    const QByteArray data = entry.file->data();
    return out.open(QIODevice::WriteOnly) && out.write(data) == data.size();
}

bool isSymbolicLink(const ArchiveFile &entry)
{
    return !entry.file->symLinkTarget().isEmpty();
}

bool writeArchiveFiles(const ArchiveListing &listing, const QString &directory, QString *error)
{
    const QDir target(directory);
    for (const ArchiveFile &entry : listing.files) {
        if (!isSymbolicLink(entry) && !writeArchiveFile(entry, target))
            return report(error, QCoreApplication::translate("ExtensionPackage", "Cannot write %1").arg(entry.path));
    }
    return true;
}

}

bool ExtensionPackage::unpack(const QString &zipPath, const QString &directory, QString *error)
{
    KZip zip(zipPath);
    if (!zip.open(QIODevice::ReadOnly) || !zip.directory())
        return report(error, QCoreApplication::translate("ExtensionPackage", "The file is not a valid ZIP archive"));
    ArchiveListing listing;
    listDirectory(zip.directory(), QString(), listing);
    if (!listing.error.isEmpty())
        return report(error, listing.error);
    if (!QDir().mkpath(directory))
        return report(error, QCoreApplication::translate("ExtensionPackage", "Cannot create %1").arg(directory));
    return writeArchiveFiles(listing, directory, error);
}
