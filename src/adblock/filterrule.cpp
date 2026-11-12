#include "adblock/filterrule.h"

#include "adblock/filteroptions.h"

#include <algorithm>

namespace {
constexpr int kDefaultTypeMask = FilterEngine::SubFrame | FilterEngine::Stylesheet
        | FilterEngine::Script | FilterEngine::Image | FilterEngine::XmlHttpRequest
        | FilterEngine::Other;

bool isCosmeticRule(const QString &line)
{
    const QStringList markers = {QStringLiteral("##"), QStringLiteral("#@#"),
                                 QStringLiteral("#?#"), QStringLiteral("#$#")};
    return std::any_of(markers.begin(), markers.end(),
                       [&line](const QString &marker) { return line.contains(marker); });
}

bool isSkippedLine(const QString &line)
{
    return line.isEmpty() || line.startsWith(QLatin1Char('!')) || line.startsWith(QLatin1Char('['))
            || isCosmeticRule(line);
}

bool isRegexRule(const QString &line)
{
    return line.size() > 1 && line.startsWith(QLatin1Char('/')) && line.endsWith(QLatin1Char('/'));
}

bool takeExceptionPrefix(QString &line)
{
    const bool isException = line.startsWith(QLatin1String("@@"));
    if (isException)
        line = line.mid(2);
    return isException;
}

bool applyTrailingOptions(QString &line, FilterRule &rule)
{
    const int dollar = line.lastIndexOf(QLatin1Char('$'));
    if (dollar < 0)
        return true;
    const QString options = line.mid(dollar + 1);
    line.truncate(dollar);
    return applyFilterOptions(options, rule);
}

bool takeStartAnchor(QString &line, FilterRule &rule)
{
    if (line.startsWith(QLatin1String("||"))) {
        line = line.mid(2);
        return true;
    }
    rule.anchorStart = line.startsWith(QLatin1Char('|'));
    if (rule.anchorStart)
        line = line.mid(1);
    return false;
}

void takeEndAnchor(QString &line, FilterRule &rule)
{
    rule.anchorEnd = line.endsWith(QLatin1Char('|'));
    if (rule.anchorEnd)
        line.chop(1);
}

int hostEnd(const QString &line)
{
    const QString terminators = QStringLiteral("^/*:?|");
    int end = 0;
    while (end < line.size() && !terminators.contains(line.at(end)))
        ++end;
    return end;
}

std::optional<FilterRule> splitHost(const QString &line, FilterRule rule)
{
    const int end = hostEnd(line);
    rule.host = line.left(end);
    if (!rule.host.contains(QLatin1Char('.')))
        return std::nullopt;
    rule.pattern = line.mid(end);
    rule.anchorStart = true;
    return rule;
}

std::optional<FilterRule> finishPattern(QString line, FilterRule rule)
{
    const bool isDomainAnchor = takeStartAnchor(line, rule);
    takeEndAnchor(line, rule);
    if (line.isEmpty())
        return std::nullopt;
    if (isDomainAnchor)
        return splitHost(line, rule);
    rule.pattern = line;
    return rule;
}
}

std::optional<FilterRule> parseFilterRule(const QString &input)
{
    QString line = input.trimmed();
    if (isSkippedLine(line))
        return std::nullopt;
    FilterRule rule;
    rule.exception = takeExceptionPrefix(line);
    if (!applyTrailingOptions(line, rule) || isRegexRule(line))
        return std::nullopt;
    if (rule.typeMask == 0)
        rule.typeMask = kDefaultTypeMask;
    return finishPattern(line.toLower(), rule);
}
