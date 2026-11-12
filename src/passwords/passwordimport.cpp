#include "passwords/passwordimport.h"

#include "passwords/passwordstore.h"

#include <QHash>
#include <QRegularExpression>
#include <QStringList>

namespace PasswordImport {

namespace {

// RFC 4180 with LF/CRLF line ends. Blank lines are dropped.
QList<QStringList> parseCsv(const QByteArray &data)
{
    QString text = QString::fromUtf8(data);
    if (text.startsWith(QChar(0xFEFF)))
        text.remove(0, 1);

    QList<QStringList> rows;
    QStringList row;
    QString field;
    bool inQuotes = false;
    bool rowHasContent = false;

    auto endField = [&] {
        row.append(field);
        field.clear();
    };
    auto endRow = [&] {
        endField();
        if (rowHasContent)
            rows.append(row);
        row.clear();
        rowHasContent = false;
    };

    for (qsizetype i = 0; i < text.size(); ++i) {
        const QChar c = text.at(i);
        if (inQuotes) {
            if (c == QLatin1Char('"')) {
                if (i + 1 < text.size() && text.at(i + 1) == QLatin1Char('"')) {
                    field.append(QLatin1Char('"'));
                    ++i;
                } else {
                    inQuotes = false;
                }
            } else {
                field.append(c);
            }
            continue;
        }
        if (c == QLatin1Char('"')) {
            inQuotes = true;
            rowHasContent = true;
        } else if (c == QLatin1Char(',')) {
            endField();
            rowHasContent = true;
        } else if (c == QLatin1Char('\n')) {
            endRow();
        } else if (c == QLatin1Char('\r')) {
            if (i + 1 < text.size() && text.at(i + 1) == QLatin1Char('\n'))
                ++i;
            endRow();
        } else {
            field.append(c);
            rowHasContent = true;
        }
    }
    if (rowHasContent || !field.isEmpty() || !row.isEmpty())
        endRow();
    return rows;
}

int findColumn(const QStringList &header, const QStringList &names)
{
    for (int i = 0; i < header.size(); ++i) {
        if (names.contains(header.at(i)))
            return i;
    }
    return -1;
}

QString cell(const QStringList &row, int column)
{
    return column >= 0 && column < row.size() ? row.at(column) : QString();
}

Format detectFormat(const QStringList &header)
{
    if (header.contains(QLatin1String("login_password")))
        return Format::Bitwarden;
    if (header.contains(QLatin1String("otpauth")) && header.contains(QLatin1String("title")))
        return Format::OnePassword;
    if (header.contains(QLatin1String("formactionorigin")) || header.contains(QLatin1String("httprealm")))
        return Format::Firefox;
    if (header.contains(QLatin1String("group")) && header.contains(QLatin1String("title")))
        return Format::KeePassXC;
    const QStringList chrome{QStringLiteral("name"), QStringLiteral("url"), QStringLiteral("username"),
                             QStringLiteral("password")};
    if (header == chrome || header == chrome + QStringList{QStringLiteral("note")})
        return Format::Chrome;
    return Format::Csv;
}

}

QString formatName(Format format)
{
    switch (format) {
    case Format::Bitwarden:
        return QStringLiteral("Bitwarden");
    case Format::OnePassword:
        return QStringLiteral("1Password");
    case Format::Firefox:
        return QStringLiteral("Firefox");
    case Format::Chrome:
        return QStringLiteral("Chrome");
    case Format::KeePassXC:
        return QStringLiteral("KeePassXC");
    case Format::Csv:
        break;
    }
    return QStringLiteral("CSV");
}

Result parse(const QByteArray &csv)
{
    Result result;
    const QList<QStringList> rows = parseCsv(csv);
    if (rows.isEmpty()) {
        result.error = Error::Empty;
        return result;
    }

    QStringList header;
    for (const QString &name : rows.first())
        header.append(name.trimmed().toLower());

    const int siteColumn = findColumn(header, {QStringLiteral("url"), QStringLiteral("login_uri"),
                                               QStringLiteral("website"), QStringLiteral("uri"),
                                               QStringLiteral("web site"), QStringLiteral("login url")});
    const int userColumn = findColumn(header, {QStringLiteral("username"), QStringLiteral("login_username"),
                                               QStringLiteral("user name"), QStringLiteral("login"),
                                               QStringLiteral("login name")});
    const int passwordColumn = findColumn(header, {QStringLiteral("password"), QStringLiteral("login_password")});
    if (siteColumn < 0 || userColumn < 0 || passwordColumn < 0) {
        result.error = Error::NotPasswordExport;
        return result;
    }
    if (rows.size() < 2) {
        result.error = Error::Empty;
        return result;
    }

    result.format = detectFormat(header);
    const int typeColumn = header.indexOf(QStringLiteral("type"));

    // origin + "\n" + username -> index in result.logins
    QHash<QString, int> seen;
    for (qsizetype r = 1; r < rows.size(); ++r) {
        const QStringList &row = rows.at(r);

        if (typeColumn >= 0 && cell(row, typeColumn).trimmed().toLower() != QLatin1String("login")) {
            ++result.skippedNotLogin;
            continue;
        }

        QStringList origins;
        const QStringList parts = cell(row, siteColumn).split(QRegularExpression(QStringLiteral("[,\r\n]")));
        for (const QString &part : parts) {
            const QString origin = PasswordStore::originFromInput(part);
            if (!origin.isEmpty() && !origins.contains(origin))
                origins.append(origin);
        }
        if (origins.isEmpty()) {
            ++result.skippedNoSite;
            continue;
        }

        const QString username = cell(row, userColumn);
        const QString password = cell(row, passwordColumn);
        if (username.isEmpty() || password.isEmpty()) {
            ++result.skippedNoCredentials;
            continue;
        }

        for (const QString &origin : origins) {
            const QString key = origin + QLatin1Char('\n') + username;
            const auto it = seen.constFind(key);
            if (it != seen.constEnd()) {
                result.logins[it.value()].password = password;
            } else {
                seen.insert(key, int(result.logins.size()));
                result.logins.append({origin, username, password});
            }
        }
    }
    return result;
}

}
