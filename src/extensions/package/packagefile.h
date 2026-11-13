#pragma once

#include <QString>

#include "extensions/package/extensionpackage.h"

struct PackageFile {
    QString zipPath;
    QString source;
    QString label;
    bool isTemporary = false;
};

struct StagedPackage {
    QString directory;
    ExtensionPackage package;
    PackageFile file;
};
