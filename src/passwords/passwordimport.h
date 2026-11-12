#pragma once

#include <QByteArray>
#include <QList>
#include <QString>

namespace PasswordImport {

enum class Format { Bitwarden, OnePassword, Firefox, Chrome, KeePassXC, Csv };
enum class Error { None, NotPasswordExport, Empty };

struct Login
{
    QString origin;
    QString username;
    QString password;
};

struct Result
{
    Format format = Format::Csv;
    QList<Login> logins;
    int skippedNoSite = 0;
    int skippedNoCredentials = 0;
    int skippedNotLogin = 0;
    Error error = Error::None;
};

Result parse(const QByteArray &csv);

QString formatName(Format format);

}
