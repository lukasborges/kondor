#include "passwords/passwordimportfile.h"

#include <QFile>
#include <QFileInfo>

namespace {

constexpr qint64 kMaxImportBytes = 20 * 1024 * 1024;

ImportFile failure(const char *error)
{
    return {QByteArray(), QLatin1String(error)};
}

ImportFile readWithinLimit(QFile &source)
{
    QByteArray data = source.read(kMaxImportBytes + 1);
    if (data.size() <= kMaxImportBytes)
        return {data, QString()};
    data.fill('\0');
    return failure("tooLarge");
}

}

ImportFile readImportFile(const QUrl &file)
{
    QFile source(file.toLocalFile());
    if (!file.isLocalFile() || !QFileInfo(source).isFile())
        return failure("unreadable");
    if (source.size() > kMaxImportBytes)
        return failure("tooLarge");
    if (!source.open(QIODevice::ReadOnly))
        return failure("unreadable");
    return readWithinLimit(source);
}
