#pragma once

#include <QString>

QString normalizedUserScriptVersion(const QString &raw);
bool isNewerUserScriptVersion(const QString &candidate, const QString &installed);
