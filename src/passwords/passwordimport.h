#pragma once

#include <QByteArray>
#include <QList>
#include <QString>

// Parser for the CSV files that other browsers and password managers export
// (Chrome-based, Firefox-based, Bitwarden, 1Password, KeePassXC, LastPass…).
// Pure logic: it never touches KWallet, so it can be unit tested.
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

// Name shown in the review dialog: "Bitwarden", "1Password", "Firefox",
// "Chrome", "KeePassXC" or "CSV".
QString formatName(Format format);

}
