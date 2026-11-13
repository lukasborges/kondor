#include "passwords/import/importinfo.h"

namespace {

QVariantMap emptyImportInfo(const QUrl &file)
{
    QVariantMap info{
        {QStringLiteral("fileName"), file.fileName()},
        {QStringLiteral("format"), QString()},
        {QStringLiteral("error"), QString()},
    };
    for (const char *key : {"newCount", "identicalCount", "conflictCount", "conflictSites",
                            "skippedNoSite", "skippedNoCredentials", "skippedNotLogin"})
        info.insert(QLatin1String(key), 0);
    return info;
}

}

QVariantMap importFailure(const QUrl &file, const QString &error)
{
    QVariantMap info = emptyImportInfo(file);
    info.insert(QStringLiteral("error"), error);
    return info;
}

QString importErrorName(PasswordImport::Error error)
{
    switch (error) {
    case PasswordImport::Error::NotPasswordExport:
        return QStringLiteral("notPasswordExport");
    case PasswordImport::Error::Empty:
        return QStringLiteral("empty");
    case PasswordImport::Error::None:
        break;
    }
    return {};
}

QVariantMap importResult(const QUrl &file, const PasswordImport::Result &parsed,
                         const ImportSummary &summary)
{
    QVariantMap info = emptyImportInfo(file);
    info.insert(QStringLiteral("format"), PasswordImport::formatName(parsed.format));
    info.insert(QStringLiteral("newCount"), summary.newCount);
    info.insert(QStringLiteral("identicalCount"), summary.identicalCount);
    info.insert(QStringLiteral("conflictCount"), summary.conflictCount);
    info.insert(QStringLiteral("conflictSites"), summary.conflictSites);
    info.insert(QStringLiteral("skippedNoSite"), parsed.skippedNoSite);
    info.insert(QStringLiteral("skippedNoCredentials"), parsed.skippedNoCredentials);
    info.insert(QStringLiteral("skippedNotLogin"), parsed.skippedNotLogin);
    return info;
}
