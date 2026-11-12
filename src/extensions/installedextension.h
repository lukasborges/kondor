#pragma once

#include <QString>

#include "extensions/extensionpackage.h"

struct InstalledExtension {
    ExtensionPackage package;
    bool enabled = true;
    bool privateAllowed = false;
    QString source;
    QString token;
    bool updateAvailable = false;
    bool updateNeedsReview = false;
};
