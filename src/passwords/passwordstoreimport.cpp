#include "passwords/passwordstore.h"

#include "passwords/import/importinfo.h"

#include <QFile>

std::optional<SavedLogins> PasswordStore::importSavedLogins() const
{
    const auto folder = openFolder();
    if (!folder)
        return std::nullopt;
    return folder->allLogins();
}

bool PasswordStore::writeImportedLogins(const QString &origin, const QMap<QString, QString> &logins) const
{
    const auto folder = openFolder();
    return folder && folder->writeLogins(origin, logins);
}

void PasswordStore::prepareImport(const QUrl &file)
{
    if (isImportRunning())
        return;
    m_importFileName = file.fileName();
    if (openFolder())
        m_preparation.start(file);
    else
        emit importPrepared(importFailure(file, QStringLiteral("walletUnavailable")));
}

void PasswordStore::commitImport(bool replaceConflicts)
{
    if (isImportRunning())
        return;
    startImportCommit(replaceConflicts);
}

void PasswordStore::startImportCommit(bool replaceConflicts)
{
    auto write = [this](const QString &origin, const QMap<QString, QString> &logins) {
        return writeImportedLogins(origin, logins);
    };
    PendingImport pending = m_preparation.takePending();
    pending.replaceConflicts = replaceConflicts;
    m_commit = new ImportCommit(std::move(pending), write, this);
    connect(m_commit, &ImportCommit::progressed, this, &PasswordStore::importDoneChanged);
    connect(m_commit, &ImportCommit::finished, this, &PasswordStore::finishImportCommit);
    emitImportProgressChanged();
    m_commit->start();
}

void PasswordStore::emitImportProgressChanged()
{
    emit importRunningChanged();
    emit importDoneChanged();
    emit importTotalChanged();
}

void PasswordStore::finishImportCommit(int written)
{
    m_commit->deleteLater();
    m_commit = nullptr;
    notifyLoginsChanged();
    m_importOutcome.record(written, m_importFileName);
    emitImportProgressChanged();
    emit importFinished(written);
}

void PasswordStore::cancelImport()
{
    m_preparation.cancel();
    m_preparation.takePending();
}

void PasswordStore::setImportPageOpen(bool isOpen)
{
    m_importOutcome.setPageOpen(isOpen);
}

QVariantMap PasswordStore::takeImportResult()
{
    return m_importOutcome.take();
}

QVariantMap PasswordStore::claimImportNotification()
{
    return m_importOutcome.claimNotification();
}

bool PasswordStore::moveImportFileToTrash(const QUrl &file)
{
    return file.isLocalFile() && QFile::moveToTrash(file.toLocalFile());
}
