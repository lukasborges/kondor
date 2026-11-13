#pragma once

#include <QString>
#include <QStringList>
#include <QVariantList>

namespace PermissionDescription {

struct PatternParts {
    QString scheme;
    QString host;
    bool all = false;
};

PatternParts parsePattern(const QString &pattern);
QVariantList permissionEntries(const QStringList &matches, const QStringList &permissions,
                               const QStringList &includes);
QStringList permissionLines(const QStringList &matches, const QStringList &permissions,
                            const QStringList &includes);

}
