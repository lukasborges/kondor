#pragma once

#include <QString>

#include <optional>

#include "extensions/packagefile.h"

class ExtensionInstaller
{
public:
    explicit ExtensionInstaller(const QString &extensionsDirectory);

    std::optional<StagedPackage> stage(const PackageFile &file, QString &error) const;
    bool commit(const StagedPackage &staged, QString &error) const;
    void discard(const StagedPackage &staged) const;

private:
    QString finalDirectoryOf(const QString &id) const;
    bool moveToNew(const StagedPackage &staged, const QString &finalDirectory, QString &error) const;
    bool moveIntoPlace(const QString &finalDirectory, QString &error) const;
    bool replaceExisting(const QString &finalDirectory, QString &error) const;

    QString m_extensionsDirectory;
};
