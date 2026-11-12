#include "passwords/passwordimport.h"

#include "passwords/csvreader.h"
#include "passwords/passwordimportcolumns.h"
#include "passwords/passwordorigin.h"

#include <QHash>
#include <QRegularExpression>
#include <QStringList>

namespace PasswordImport {

namespace {

QString cell(const QStringList &row, int column)
{
    return column >= 0 && column < row.size() ? row.at(column) : QString();
}

QStringList originsIn(const QString &sites)
{
    QStringList origins;
    for (const QString &part : sites.split(QRegularExpression(QStringLiteral("[,\r\n]")))) {
        const QString origin = PasswordOrigin::originFromInput(part);
        if (!origin.isEmpty() && !origins.contains(origin))
            origins.append(origin);
    }
    return origins;
}

class RowReader
{
public:
    RowReader(Format format, const Columns &columns)
        : m_columns(columns)
    {
        m_result.format = format;
    }

    void addRow(const QStringList &row)
    {
        if (isNotLogin(row))
            ++m_result.skippedNotLogin;
        else
            addLoginRow(row);
    }

    Result result() const { return m_result; }

private:
    bool isNotLogin(const QStringList &row) const
    {
        return m_columns.type >= 0 && cell(row, m_columns.type).trimmed().toLower() != QLatin1String("login");
    }

    void addLoginRow(const QStringList &row)
    {
        const QStringList origins = originsIn(cell(row, m_columns.site));
        if (origins.isEmpty())
            ++m_result.skippedNoSite;
        else
            addCredentials(origins, cell(row, m_columns.user), cell(row, m_columns.password));
    }

    void addCredentials(const QStringList &origins, const QString &username, const QString &password)
    {
        if (username.isEmpty() || password.isEmpty()) {
            ++m_result.skippedNoCredentials;
            return;
        }
        for (const QString &origin : origins)
            addLogin({origin, username, password});
    }

    void addLogin(const Login &login)
    {
        const QString key = login.origin + QLatin1Char('\n') + login.username;
        const auto it = m_seen.constFind(key);
        if (it != m_seen.constEnd()) {
            m_result.logins[it.value()].password = login.password;
            return;
        }
        m_seen.insert(key, int(m_result.logins.size()));
        m_result.logins.append(login);
    }

    Columns m_columns;
    Result m_result;
    QHash<QString, int> m_seen;
};

Result failure(Error error)
{
    Result result;
    result.error = error;
    return result;
}

Result readRows(const QList<QStringList> &rows, const QStringList &header, const Columns &columns)
{
    RowReader reader(detectFormat(header), columns);
    for (qsizetype i = 1; i < rows.size(); ++i)
        reader.addRow(rows.at(i));
    return reader.result();
}

}

QString formatName(Format format)
{
    static const QStringList names{QStringLiteral("Bitwarden"), QStringLiteral("1Password"),
                                   QStringLiteral("Firefox"), QStringLiteral("Chrome"),
                                   QStringLiteral("KeePassXC"), QStringLiteral("CSV")};
    return names.at(int(format));
}

Result parse(const QByteArray &csv)
{
    const QList<QStringList> rows = readCsvRows(csv);
    if (rows.isEmpty())
        return failure(Error::Empty);
    const QStringList header = normalizedHeader(rows.first());
    const Columns columns = findColumns(header);
    if (!columns.isComplete())
        return failure(Error::NotPasswordExport);
    if (rows.size() < 2)
        return failure(Error::Empty);
    return readRows(rows, header, columns);
}

}
