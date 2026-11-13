#include "passwords/import/importcommit.h"

#include <QTimer>

namespace {

QMap<QString, QList<PasswordImport::Login>> groupByOrigin(const QList<PasswordImport::Login> &logins)
{
    QMap<QString, QList<PasswordImport::Login>> byOrigin;
    for (const PasswordImport::Login &login : logins)
        byOrigin[login.origin].append(login);
    return byOrigin;
}

}

ImportCommit::ImportCommit(PendingImport pending, Writer write, QObject *parent)
    : QObject(parent)
    , m_byOrigin(groupByOrigin(pending.logins))
    , m_origins(m_byOrigin.keys())
    , m_saved(std::move(pending.saved))
    , m_replaceConflicts(pending.replaceConflicts)
    , m_write(std::move(write))
{
}

void ImportCommit::start()
{
    scheduleNext();
}

void ImportCommit::scheduleNext()
{
    QTimer::singleShot(0, this, &ImportCommit::writeNextOrigin);
}

void ImportCommit::writeNextOrigin()
{
    if (m_done == total())
        return emit finished(m_written);
    const int changes = mergeOrigin(m_origins.at(m_done));
    if (changes < 0)
        return emit finished(-1);
    m_written += changes;
    ++m_done;
    emit progressed();
    scheduleNext();
}

int ImportCommit::mergeOrigin(const QString &origin)
{
    QMap<QString, QString> saved = m_saved.value(origin);
    const int changes = mergeLogins(saved, m_byOrigin.value(origin), m_replaceConflicts);
    if (changes == 0)
        return 0;
    return m_write(origin, saved) ? changes : -1;
}
