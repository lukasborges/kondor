#pragma once

#include <QHash>
#include <QList>
#include <QString>
#include <QStringList>
#include <QUrl>

// Network filter rules in a pragmatic subset of the Adblock Plus syntax, enough
// for EasyList and EasyPrivacy. Cosmetic rules, regex rules and rules with
// unknown options are skipped. Immutable once built, so one instance can be
// shared by the request interceptor (IO thread) while the next one is parsed.
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

    // Parses one list (one rule per line) and adds its network rules.
    void addList(const QByteArray &text);
    // Parses a single line; returns false when it is not a usable network rule.
    bool addRule(const QString &line);

    int ruleCount() const { return m_ruleCount; }

    // True when the request is blocked: a blocking rule matches and no
    // exception rule does. `firstPartyHost` is the host of the page (may be empty).
    bool shouldBlock(const QUrl &url, const QString &firstPartyHost, ResourceKind kind) const;

private:
    struct Rule {
        QString pattern;            // lower case; may contain '*' and '^'
        bool anchorStart = false;   // pattern must match at the start
        bool anchorEnd = false;     // pattern must match at the end
        bool exception = false;
        int typeMask = 0;
        enum ThirdParty { Any, OnlyThirdParty, OnlyFirstParty } thirdParty = Any;
        QStringList domainsInclude;
        QStringList domainsExclude;
    };
    struct Request {
        QString url;       // lower case, fully encoded
        QString rest;      // url after the host (":8080/path?q")
        QString host;
        QString firstPartyHost;
        bool thirdParty = false;
        int kind = 0;
    };

    static bool matchesPattern(const Rule &rule, const QString &text, bool unanchoredSearch);
    static bool optionsMatch(const Rule &rule, const Request &request);
    bool matchesAny(const Request &request, bool exceptions) const;

    // `||host…` rules by host; the pattern holds what follows the host.
    QHash<QString, QList<Rule>> m_domainRules;
    // Other rules indexed by a token of the pattern that must appear in the URL.
    QHash<QString, QList<Rule>> m_tokenRules;
    QList<Rule> m_otherRules;
    int m_ruleCount = 0;
};
