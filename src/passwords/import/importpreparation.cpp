#include "passwords/import/importpreparation.h"

#include "passwords/import/importinfo.h"
#include "passwords/csv/passwordimportfile.h"

#include <QtConcurrent>

namespace {

ParsedImport readAndParse(const QUrl &file)
{
    ImportFile source = readImportFile(file);
    if (!source.error.isEmpty())
        return {source.error, {}};
    ParsedImport parsed{QString(), PasswordImport::parse(source.data)};
    source.data.fill('\0');
    return parsed;
}

}

ImportPreparation::ImportPreparation(SavedLoginsSource savedLogins, QObject *parent)
    : QObject(parent)
    , m_savedLogins(std::move(savedLogins))
{
    connect(&m_watcher, &QFutureWatcher<ParsedImport>::finished, this, &ImportPreparation::finish);
}

void ImportPreparation::start(const QUrl &file)
{
    m_pending = {};
    m_file = file;
    m_watcher.setFuture(QtConcurrent::run(readAndParse, file));
    emit runningChanged();
}

void ImportPreparation::cancel()
{
    m_pending = {};
    if (!isRunning())
        return;
    m_watcher.setFuture(QFuture<ParsedImport>());
    emit runningChanged();
}

PendingImport ImportPreparation::takePending()
{
    return std::exchange(m_pending, {});
}

void ImportPreparation::finish()
{
    if (!m_watcher.future().isValid())
        return;
    const QVariantMap info = describe(m_watcher.result());
    emit runningChanged();
    emit prepared(info);
}

QVariantMap ImportPreparation::describe(const ParsedImport &source)
{
    if (!source.error.isEmpty())
        return importFailure(m_file, source.error);
    const QString error = importErrorName(source.parsed.error);
    if (!error.isEmpty())
        return importFailure(m_file, error);
    const auto saved = m_savedLogins();
    if (!saved)
        return importFailure(m_file, QStringLiteral("walletUnavailable"));
    m_pending = {source.parsed.logins, *saved};
    return importResult(m_file, source.parsed, summarizeImport(source.parsed.logins, *saved));
}
