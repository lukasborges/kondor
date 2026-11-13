#include "extensions/install/extensioninstaller.h"

#include <QCoreApplication>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QUuid>

namespace {

void removeDirectory(const QString &directory)
{
    QDir(directory).removeRecursively();
}

QString newDirectoryOf(const QString &finalDirectory)
{
    return finalDirectory + QStringLiteral(".new");
}

QString oldDirectoryOf(const QString &finalDirectory)
{
    return finalDirectory + QStringLiteral(".old");
}

bool abandonNew(const QString &finalDirectory)
{
    removeDirectory(newDirectoryOf(finalDirectory));
    return false;
}

std::optional<ExtensionPackage> unpackAndLoad(const QString &zipPath, const QString &directory,
                                              QString &error)
{
    if (ExtensionPackage::unpack(zipPath, directory, &error)) {
        const ExtensionPackage package = ExtensionPackage::load(directory, &error);
        if (package.isValid())
            return package;
    }
    removeDirectory(directory);
    return std::nullopt;
}

QString stagingDirectoryIn(const QString &base)
{
    return base + QStringLiteral("/.staging-") + QUuid::createUuid().toString(QUuid::WithoutBraces);
}

}

ExtensionInstaller::ExtensionInstaller(const QString &extensionsDirectory)
    : m_extensionsDirectory(extensionsDirectory)
{
}

QString ExtensionInstaller::finalDirectoryOf(const QString &id) const
{
    return m_extensionsDirectory + QLatin1Char('/') + id;
}

std::optional<StagedPackage> ExtensionInstaller::stage(const PackageFile &file, QString &error) const
{
    if (!QDir().mkpath(m_extensionsDirectory)) {
        error = QCoreApplication::translate("ExtensionManager", "Cannot create %1")
                    .arg(m_extensionsDirectory);
        return std::nullopt;
    }
    const QString directory = stagingDirectoryIn(m_extensionsDirectory);
    const auto package = unpackAndLoad(file.zipPath, directory, error);
    if (!package)
        return std::nullopt;
    return StagedPackage{directory, *package, file};
}

bool ExtensionInstaller::replaceExisting(const QString &finalDirectory, QString &error) const
{
    if (!QFileInfo::exists(finalDirectory))
        return true;
    if (QDir().rename(finalDirectory, oldDirectoryOf(finalDirectory)))
        return true;
    error = QCoreApplication::translate("ExtensionManager", "Cannot replace %1").arg(finalDirectory);
    return false;
}

bool ExtensionInstaller::moveToNew(const StagedPackage &staged, const QString &finalDirectory,
                                   QString &error) const
{
    if (QDir().rename(staged.directory, newDirectoryOf(finalDirectory)))
        return true;
    error = QCoreApplication::translate("ExtensionManager", "Cannot install into %1")
                .arg(newDirectoryOf(finalDirectory));
    return false;
}

bool ExtensionInstaller::moveIntoPlace(const QString &finalDirectory, QString &error) const
{
    if (!replaceExisting(finalDirectory, error))
        return abandonNew(finalDirectory);
    if (QDir().rename(newDirectoryOf(finalDirectory), finalDirectory))
        return true;
    if (QFileInfo::exists(oldDirectoryOf(finalDirectory)))
        QDir().rename(oldDirectoryOf(finalDirectory), finalDirectory);
    error = QCoreApplication::translate("ExtensionManager", "Cannot install into %1")
                .arg(finalDirectory);
    return abandonNew(finalDirectory);
}

bool ExtensionInstaller::commit(const StagedPackage &staged, QString &error) const
{
    const QString finalDirectory = finalDirectoryOf(staged.package.id());
    removeDirectory(newDirectoryOf(finalDirectory));
    removeDirectory(oldDirectoryOf(finalDirectory));
    if (!moveToNew(staged, finalDirectory, error) || !moveIntoPlace(finalDirectory, error))
        return false;
    removeDirectory(oldDirectoryOf(finalDirectory));
    return true;
}

void ExtensionInstaller::discard(const StagedPackage &staged) const
{
    removeDirectory(staged.directory);
    if (staged.file.isTemporary)
        QFile::remove(staged.file.zipPath);
}
