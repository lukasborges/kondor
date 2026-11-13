#pragma once

#include "adblock/filters/filterrule.h"

#include <QHash>
#include <QList>
#include <QString>
#include <QUrl>

struct FilterRequest;

class FilterEngine
{
public:
    enum ResourceKind {
        MainFrame = 1 << 0,
        SubFrame = 1 << 1,
        Stylesheet = 1 << 2,
        Script = 1 << 3,
        Image = 1 << 4,
        XmlHttpRequest = 1 << 5,
        Other = 1 << 6,
    };

    void addList(const QByteArray &text);
    bool addRule(const QString &line);
    int ruleCount() const { return m_ruleCount; }
    bool shouldBlock(const QUrl &url, const QString &firstPartyHost, ResourceKind kind) const;

private:
    void indexRule(const FilterRule &rule);
    bool matchesAny(const FilterRequest &request, bool exceptions) const;
    bool matchesHostRules(const QString &host, const FilterRequest &request, bool exceptions) const;
    bool matchesDomainRules(const FilterRequest &request, bool exceptions) const;
    bool matchesTokenRules(const FilterRequest &request, bool exceptions) const;

    QHash<QString, QList<FilterRule>> m_domainRules;
    QHash<QString, QList<FilterRule>> m_tokenRules;
    QList<FilterRule> m_otherRules;
    int m_ruleCount = 0;
};
