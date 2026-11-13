#include "passwords/passwordimportplan.h"

#include <QSet>

namespace {

class ImportCounter
{
public:
    void add(const PasswordImport::Login &login, const QMap<QString, QString> &saved)
    {
        if (!saved.contains(login.username))
            ++m_summary.newCount;
        else if (saved.value(login.username) == login.password)
            ++m_summary.identicalCount;
        else
            addConflict(login.origin);
    }

    ImportSummary summary() const
    {
        ImportSummary result = m_summary;
        result.conflictSites = int(m_conflictOrigins.size());
        return result;
    }

private:
    void addConflict(const QString &origin)
    {
        ++m_summary.conflictCount;
        m_conflictOrigins.insert(origin);
    }

    ImportSummary m_summary;
    QSet<QString> m_conflictOrigins;
};

bool shouldWrite(const QMap<QString, QString> &saved, const PasswordImport::Login &login,
                 bool replaceConflicts)
{
    if (!saved.contains(login.username))
        return true;
    return replaceConflicts && saved.value(login.username) != login.password;
}

}

ImportSummary summarizeImport(const QList<PasswordImport::Login> &logins, const SavedLogins &saved)
{
    ImportCounter counter;
    for (const PasswordImport::Login &login : logins)
        counter.add(login, saved.value(login.origin));
    return counter.summary();
}

int mergeLogins(QMap<QString, QString> &saved, const QList<PasswordImport::Login> &logins,
                bool replaceConflicts)
{
    int changes = 0;
    for (const PasswordImport::Login &login : logins) {
        if (!shouldWrite(saved, login, replaceConflicts))
            continue;
        saved.insert(login.username, login.password);
        ++changes;
    }
    return changes;
}
