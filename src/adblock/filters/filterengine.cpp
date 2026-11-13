#include "adblock/filterengine.h"

#include "adblock/filteroptions.h"
#include "adblock/filterpattern.h"
#include "adblock/filterrequest.h"

#include <algorithm>

namespace {
bool isFilterableScheme(const QUrl &url)
{
    const QStringList schemes = {QStringLiteral("http"), QStringLiteral("https"),
                                 QStringLiteral("ws"), QStringLiteral("wss")};
    return schemes.contains(url.scheme());
}

QString parentDomain(const QString &host)
{
    const int dot = host.indexOf(QLatin1Char('.'));
    return dot < 0 ? QString() : host.mid(dot + 1);
}

bool domainRuleMatches(const FilterRule &rule, const FilterRequest &request, bool exceptions)
{
    return rule.exception == exceptions && optionsMatch(rule, request)
            && (rule.pattern.isEmpty() || matchesPattern(rule, request.rest, false));
}

bool searchRuleMatches(const FilterRule &rule, const FilterRequest &request, bool exceptions)
{
    return rule.exception == exceptions && optionsMatch(rule, request)
            && matchesPattern(rule, request.url, true);
}

bool anySearchRuleMatches(const QList<FilterRule> &rules, const FilterRequest &request,
                          bool exceptions)
{
    return std::any_of(rules.begin(), rules.end(), [&](const FilterRule &rule) {
        return searchRuleMatches(rule, request, exceptions);
    });
}
}

void FilterEngine::addList(const QByteArray &text)
{
    const QList<QByteArray> lines = text.split('\n');
    for (const QByteArray &line : lines)
        addRule(QString::fromUtf8(line));
}

bool FilterEngine::addRule(const QString &line)
{
    const std::optional<FilterRule> rule = parseFilterRule(line);
    if (!rule)
        return false;
    indexRule(*rule);
    ++m_ruleCount;
    return true;
}

void FilterEngine::indexRule(const FilterRule &rule)
{
    if (!rule.host.isEmpty()) {
        m_domainRules[rule.host].append(rule);
        return;
    }
    const QString token = tokenOf(rule.pattern, rule.anchorStart, rule.anchorEnd);
    if (token.isEmpty())
        m_otherRules.append(rule);
    else
        m_tokenRules[token].append(rule);
}

bool FilterEngine::matchesHostRules(const QString &host, const FilterRequest &request,
                                    bool exceptions) const
{
    const QList<FilterRule> rules = m_domainRules.value(host);
    return std::any_of(rules.begin(), rules.end(), [&](const FilterRule &rule) {
        return domainRuleMatches(rule, request, exceptions);
    });
}

bool FilterEngine::matchesDomainRules(const FilterRequest &request, bool exceptions) const
{
    for (QString host = request.host; !host.isEmpty(); host = parentDomain(host)) {
        if (matchesHostRules(host, request, exceptions))
            return true;
    }
    return false;
}

bool FilterEngine::matchesTokenRules(const FilterRequest &request, bool exceptions) const
{
    const QSet<QString> tokens = urlTokens(request.url);
    return std::any_of(tokens.begin(), tokens.end(), [&](const QString &token) {
        return anySearchRuleMatches(m_tokenRules.value(token), request, exceptions);
    });
}

bool FilterEngine::matchesAny(const FilterRequest &request, bool exceptions) const
{
    return matchesDomainRules(request, exceptions) || matchesTokenRules(request, exceptions)
            || anySearchRuleMatches(m_otherRules, request, exceptions);
}

bool FilterEngine::shouldBlock(const QUrl &url, const QString &firstPartyHost,
                               ResourceKind kind) const
{
    if (kind == MainFrame || m_ruleCount == 0 || !isFilterableScheme(url))
        return false;
    const FilterRequest request = makeFilterRequest(url, firstPartyHost, kind);
    return matchesAny(request, false) && !matchesAny(request, true);
}
