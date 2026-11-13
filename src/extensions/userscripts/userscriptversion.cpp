#include "extensions/userscripts/userscriptversion.h"

#include <QStringList>

namespace {

constexpr int kNormalizedParts = 3;

struct VersionPart {
    qlonglong number = 0;
    QString rest;
};

QString leadingDigits(const QString &part)
{
    qsizetype length = 0;
    while (length < part.size() && part.at(length).isDigit())
        ++length;
    return part.left(length);
}

VersionPart partOf(const QStringList &parts, qsizetype index)
{
    if (index >= parts.size())
        return {};
    const QString digits = leadingDigits(parts.at(index));
    return {digits.toLongLong(), parts.at(index).mid(digits.size())};
}

int comparePart(const VersionPart &candidate, const VersionPart &installed)
{
    if (candidate.number != installed.number)
        return candidate.number < installed.number ? -1 : 1;
    return QString::compare(candidate.rest, installed.rest);
}

}

QString normalizedUserScriptVersion(const QString &raw)
{
    const QStringList parts = raw.split(QLatin1Char('.'));
    QStringList normalized;
    for (qsizetype i = 0; i < kNormalizedParts; ++i)
        normalized.append(QString::number(partOf(parts, i).number));
    return normalized.join(QLatin1Char('.'));
}

bool isNewerUserScriptVersion(const QString &candidate, const QString &installed)
{
    const QStringList candidateParts = candidate.split(QLatin1Char('.'));
    const QStringList installedParts = installed.split(QLatin1Char('.'));
    const qsizetype count = qMax(candidateParts.size(), installedParts.size());
    for (qsizetype i = 0; i < count; ++i) {
        const int order = comparePart(partOf(candidateParts, i), partOf(installedParts, i));
        if (order != 0)
            return order > 0;
    }
    return false;
}
