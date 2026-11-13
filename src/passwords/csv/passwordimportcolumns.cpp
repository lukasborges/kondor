#include "passwords/passwordimportcolumns.h"

#include <algorithm>

namespace PasswordImport {

namespace {

using Names = QList<QLatin1String>;

struct FormatSignature
{
    Format format;
    Names requiredColumns;
};

const QList<FormatSignature> &formatSignatures()
{
    static const QList<FormatSignature> signatures{
        {Format::Bitwarden, {QLatin1String("login_password")}},
        {Format::OnePassword, {QLatin1String("otpauth"), QLatin1String("title")}},
        {Format::Firefox, {QLatin1String("formactionorigin")}},
        {Format::Firefox, {QLatin1String("httprealm")}},
        {Format::KeePassXC, {QLatin1String("group"), QLatin1String("title")}},
    };
    return signatures;
}

bool containsAll(const QStringList &header, const Names &names)
{
    return std::all_of(names.cbegin(), names.cend(),
                       [&header](QLatin1String name) { return header.contains(name); });
}

bool isChromeHeader(const QStringList &header)
{
    const QStringList chrome{QStringLiteral("name"), QStringLiteral("url"),
                             QStringLiteral("username"), QStringLiteral("password")};
    return header == chrome || header == chrome + QStringList{QStringLiteral("note")};
}

bool isOneOf(const QString &text, const Names &names)
{
    return std::any_of(names.cbegin(), names.cend(), [&text](QLatin1String name) { return text == name; });
}

int findColumn(const QStringList &header, const Names &names)
{
    for (int i = 0; i < header.size(); ++i) {
        if (isOneOf(header.at(i), names))
            return i;
    }
    return -1;
}

}

Format detectFormat(const QStringList &header)
{
    for (const FormatSignature &signature : formatSignatures()) {
        if (containsAll(header, signature.requiredColumns))
            return signature.format;
    }
    return isChromeHeader(header) ? Format::Chrome : Format::Csv;
}

Columns findColumns(const QStringList &header)
{
    Columns columns;
    columns.site = findColumn(header, {QLatin1String("url"), QLatin1String("login_uri"),
                                       QLatin1String("website"), QLatin1String("uri"),
                                       QLatin1String("web site"), QLatin1String("login url")});
    columns.user = findColumn(header, {QLatin1String("username"), QLatin1String("login_username"),
                                       QLatin1String("user name"), QLatin1String("login"),
                                       QLatin1String("login name")});
    columns.password = findColumn(header, {QLatin1String("password"), QLatin1String("login_password")});
    columns.type = header.indexOf(QStringLiteral("type"));
    return columns;
}

QStringList normalizedHeader(const QStringList &row)
{
    QStringList header;
    for (const QString &name : row)
        header.append(name.trimmed().toLower());
    return header;
}

}
