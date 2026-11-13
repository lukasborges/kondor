#pragma once

#include <QString>

#include "extensions/extensionpackage.h"

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
