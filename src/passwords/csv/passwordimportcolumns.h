#pragma once

#include <QStringList>

#include "passwords/passwordimport.h"

namespace PasswordImport {

struct Columns
{
    int site = -1;
    int user = -1;
    int password = -1;
    int type = -1;

    bool isComplete() const { return site >= 0 && user >= 0 && password >= 0; }
};

QStringList normalizedHeader(const QStringList &row);
Columns findColumns(const QStringList &header);
Format detectFormat(const QStringList &header);

}
