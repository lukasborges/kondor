#pragma once

#include <QString>

bool isSafeRelativePath(const QString &path);
QString packageFileError(const QString &directory, const QString &path, const QString &where);
