#include "extensions/packagesuffix.h"

bool hasPackageSuffix(const QString &path)
{
    return path.endsWith(QLatin1String(".kondorext"), Qt::CaseInsensitive);
}
