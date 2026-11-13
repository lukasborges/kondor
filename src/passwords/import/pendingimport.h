#pragma once

#include <QList>

#include "passwords/passwordimport.h"
#include "passwords/passwordimportplan.h"

struct PendingImport
{
    QList<PasswordImport::Login> logins;
    SavedLogins saved;
    bool replaceConflicts = false;
};
