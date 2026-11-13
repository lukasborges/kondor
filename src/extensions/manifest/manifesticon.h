#pragma once

#include <QString>

#include <optional>

std::optional<QString> resolveManifestIcon(const QString &directory, const QString &icon,
                                           QString &error);
