#pragma once

#include <QString>

namespace SearchEngines {

QString urlTemplate(const QString &engineId, const QString &customUrl);
QString displayName(const QString &engineId, const QString &customUrl);

}
