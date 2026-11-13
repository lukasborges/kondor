#pragma once

#include <QList>

#include "passwords/csv/passwordimport.h"
#include "passwords/csv/passwordimportplan.h"

struct PendingImport
{
    QList<PasswordImport::Login> logins;
    SavedLogins saved;
    bool replaceConflicts = false;
};
