#include "adblock/filters/filteroptions.h"

#include "adblock/filters/filterpattern.h"

#include <algorithm>

namespace {
struct TypeOption {
    QLatin1String name;
    FilterEngine::ResourceKind kind;
};

const TypeOption kTypeOptions[] = {
    {QLatin1String("script"), FilterEngine::Script},
    {QLatin1String("image"), FilterEngine::Image},
    {QLatin1String("stylesheet"), FilterEngine::Stylesheet},
    {QLatin1String("xmlhttprequest"), FilterEngine::XmlHttpRequest},
    {QLatin1String("subdocument"), FilterEngine::SubFrame},
};

int kindForOption(const QString &name)
{
    const auto *option = std::find_if(std::begin(kTypeOptions), std::end(kTypeOptions),
                                      [&name](const TypeOption &type) { return type.name == name; });
    return option == std::end(kTypeOptions) ? 0 : option->kind;
}

void addDomain(const QString &domain, FilterRule &rule)
{
    if (domain.startsWith(QLatin1Char('~')))
        rule.domainsExclude.append(domain.mid(1));
    else if (!domain.isEmpty())
        rule.domainsInclude.append(domain);
}

void addDomains(const QString &list, FilterRule &rule)
{
    const QStringList domains = list.toLower().split(QLatin1Char('|'));
    for (const QString &domain : domains)
        addDomain(domain, rule);
}

bool applyPartyOption(const QString &option, FilterRule &rule)
{
    const bool isNegated = option == QLatin1String("~third-party");
    if (!isNegated && option != QLatin1String("third-party"))
        return false;
    rule.thirdParty = isNegated ? FilterRule::OnlyFirstParty : FilterRule::OnlyThirdParty;
    return true;
}

bool applyDomainOption(const QString &option, FilterRule &rule)
{
    if (!option.startsWith(QLatin1String("domain=")))
        return false;
    addDomains(option.mid(7), rule);
    return true;
}

bool applyTypeOption(const QString &option, FilterRule &rule)
{
    const int kind = kindForOption(option);
    rule.typeMask |= kind;
    return kind != 0;
}

bool applyFilterOption(const QString &option, FilterRule &rule)
{
    return applyPartyOption(option, rule) || applyDomainOption(option, rule)
            || applyTypeOption(option, rule);
}

bool matchesAnyDomain(const QStringList &domains, const QString &host)
{
    return std::any_of(domains.begin(), domains.end(),
                       [&host](const QString &domain) { return hostMatches(host, domain); });
}

bool partyMatches(const FilterRule &rule, const FilterRequest &request)
{
    if (rule.thirdParty == FilterRule::OnlyThirdParty)
        return request.thirdParty;
    if (rule.thirdParty == FilterRule::OnlyFirstParty)
        return !request.thirdParty;
    return true;
}

bool domainsMatch(const FilterRule &rule, const FilterRequest &request)
{
    if (matchesAnyDomain(rule.domainsExclude, request.firstPartyHost))
        return false;
    return rule.domainsInclude.isEmpty()
            || matchesAnyDomain(rule.domainsInclude, request.firstPartyHost);
}
}

bool applyFilterOptions(const QString &options, FilterRule &rule)
{
    const QStringList list = options.split(QLatin1Char(','));
    return std::all_of(list.begin(), list.end(), [&rule](const QString &option) {
        return applyFilterOption(option, rule);
    });
}

bool optionsMatch(const FilterRule &rule, const FilterRequest &request)
{
    return (rule.typeMask & request.kind) && partyMatches(rule, request)
            && domainsMatch(rule, request);
}
