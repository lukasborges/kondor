#pragma once

#include <QHash>
#include <QList>
#include <QMap>
#include <QString>

#include "passwords/csv/passwordimport.h"

using SavedLogins = QHash<QString, QMap<QString, QString>>;

struct ImportSummary
{
    int newCount = 0;
    int identicalCount = 0;
    int conflictCount = 0;
    int conflictSites = 0;
};

ImportSummary summarizeImport(const QList<PasswordImport::Login> &logins, const SavedLogins &saved);

int mergeLogins(QMap<QString, QString> &saved, const QList<PasswordImport::Login> &logins,
                bool replaceConflicts);
