#include "passwords/passwordstore.h"

#include "passwords/passwordimportfile.h"
#include "passwords/passwordimportplan.h"

#include <QFile>
#include <QMap>
#include <QSet>

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

SavedLogins savedLoginsFor(const WalletFolder &folder, const QList<PasswordImport::Login> &logins)
{
    SavedLogins saved;
    for (const PasswordImport::Login &login : logins) {
        if (!saved.contains(login.origin))
            saved.insert(login.origin, folder.logins(login.origin).value_or(QMap<QString, QString>()));
    }
    return saved;
}

QMap<QString, QList<PasswordImport::Login>> groupByOrigin(const QList<PasswordImport::Login> &logins)
{
    QMap<QString, QList<PasswordImport::Login>> byOrigin;
    for (const PasswordImport::Login &login : logins)
        byOrigin[login.origin].append(login);
    return byOrigin;
}

class ImportWriter
{
public:
    ImportWriter(const WalletFolder &folder, bool replaceConflicts)
        : m_folder(folder)
        , m_replaceConflicts(replaceConflicts)
    {
    }

    int writeAll(const QList<PasswordImport::Login> &pending) const
    {
        int written = 0;
        const auto byOrigin = groupByOrigin(pending);
        for (auto it = byOrigin.cbegin(); it != byOrigin.cend(); ++it) {
            const int changes = writeOrigin(it.key(), it.value());
            if (changes < 0)
                return -1;
            written += changes;
        }
        return written;
    }

private:
    int writeOrigin(const QString &origin, const QList<PasswordImport::Login> &logins) const
    {
        QMap<QString, QString> saved = m_folder.logins(origin).value_or(QMap<QString, QString>());
        const int changes = mergeLogins(saved, logins, m_replaceConflicts);
        if (changes == 0)
            return 0;
        return m_folder.writeLogins(origin, saved) ? changes : -1;
    }

    const WalletFolder &m_folder;
    bool m_replaceConflicts;
};

}

QVariantMap PasswordStore::prepareImport(const QUrl &file)
{
    m_pendingImport.clear();
    const auto folder = openFolder();
    if (!folder)
        return importFailure(file, QStringLiteral("walletUnavailable"));
    ImportFile source = readImportFile(file);
    if (!source.error.isEmpty())
        return importFailure(file, source.error);
    PasswordImport::Result parsed = PasswordImport::parse(source.data);
    source.data.fill('\0');
    return describeImport(*folder, file, parsed);
}

QVariantMap PasswordStore::describeImport(const WalletFolder &folder, const QUrl &file,
                                          PasswordImport::Result &parsed)
{
    const QString error = importErrorName(parsed.error);
    if (!error.isEmpty())
        return importFailure(file, error);
    const ImportSummary summary = summarizeImport(parsed.logins, savedLoginsFor(folder, parsed.logins));
    m_pendingImport = std::move(parsed.logins);
    return importResult(file, parsed, summary);
}

int PasswordStore::commitImport(bool replaceConflicts)
{
    const QList<PasswordImport::Login> pending = std::exchange(m_pendingImport, {});
    const auto folder = openFolder();
    if (!folder)
        return -1;
    const int written = ImportWriter(*folder, replaceConflicts).writeAll(pending);
    notifyLoginsChanged();
    return written;
}

void PasswordStore::cancelImport()
{
    m_pendingImport.clear();
}

bool PasswordStore::moveImportFileToTrash(const QUrl &file)
{
    return file.isLocalFile() && QFile::moveToTrash(file.toLocalFile());
}
