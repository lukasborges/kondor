#pragma once

#include <QString>

struct PackageSize {
    qint64 bytes = 0;
    int files = 0;
};

PackageSize measureDirectory(const QString &directory);
QString packageLimitError(const PackageSize &size);
