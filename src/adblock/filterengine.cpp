#include "filterengine.h"

#include <QSet>

namespace {
bool isAlnum(QChar c)
{
    return (c >= QLatin1Char('a') && c <= QLatin1Char('z'))
            || (c >= QLatin1Char('0') && c <= QLatin1Char('9'));
}

// '^' matches any character that is not a letter, digit, '_', '-', '.' or '%'
// (or the end of the address).
bool isSeparator(QChar c)
{
    return !(isAlnum(c) || c == QLatin1Char('_') || c == QLatin1Char('-')
             || c == QLatin1Char('.') || c == QLatin1Char('%'));
}

// Matches `pattern` (literal characters and '^') at `pos` of `text`; returns
// the end position or -1.
int matchSegmentAt(const QString &segment, const QString &text, int pos)
{
    int t = pos;
    for (int i = 0; i < segment.size(); ++i) {
        const QChar c = segment.at(i);
        if (c == QLatin1Char('^')) {
            if (t == text.size())
                continue;       // matches the end
            if (!isSeparator(text.at(t)))
                return -1;
            ++t;
        } else {
            if (t >= text.size() || text.at(t) != c)
                return -1;
            ++t;
        }
    }
    return t;
}

QString registrableDomain(const QString &host)
{
    const QStringList labels = host.split(QLatin1Char('.'));
    int keep = 2;
    // "example.co.uk", "example.com.br": a short second-level label under a
    // two-letter TLD. A small heuristic stands in for the public suffix list.
    if (labels.size() >= 3 && labels.last().size() == 2 && labels.at(labels.size() - 2).size() <= 3)
        keep = 3;
    if (labels.size() <= keep)
        return host;
    return labels.mid(labels.size() - keep).join(QLatin1Char('.'));
}

bool hostMatches(const QString &host, const QString &domain)
{
    return host == domain || host.endsWith(QLatin1Char('.') + domain);
}

// Longest run of letters and digits (>= 3) bounded on both sides by a literal
// character or '^': it must be a whole token of any matching URL.
QString tokenOf(const QString &pattern, bool anchorStart, bool anchorEnd)
{
    QString best;
    int i = 0;
    while (i < pattern.size()) {
        if (!isAlnum(pattern.at(i))) {
            ++i;
            continue;
        }
        int j = i;
        while (j < pattern.size() && isAlnum(pattern.at(j)))
            ++j;
        const bool leftBound = i > 0 ? pattern.at(i - 1) != QLatin1Char('*') : anchorStart;
        const bool rightBound = j < pattern.size() ? pattern.at(j) != QLatin1Char('*') : anchorEnd;
        if (leftBound && rightBound && j - i >= 3 && j - i > best.size())
            best = pattern.mid(i, j - i);
        i = j;
    }
    return best;
}

QList<QString> urlTokens(const QString &url)
{
    QList<QString> tokens;
    int i = 0;
    while (i < url.size()) {
        if (!isAlnum(url.at(i))) {
            ++i;
            continue;
        }
        int j = i;
        while (j < url.size() && isAlnum(url.at(j)))
            ++j;
        if (j - i >= 3)
            tokens.append(url.mid(i, j - i));
        i = j;
    }
    return tokens;
}

int kindForOption(const QString &name)
{
    if (name == QLatin1String("script"))
        return FilterEngine::Script;
    if (name == QLatin1String("image"))
        return FilterEngine::Image;
    if (name == QLatin1String("stylesheet"))
        return FilterEngine::Stylesheet;
    if (name == QLatin1String("xmlhttprequest"))
        return FilterEngine::XmlHttpRequest;
    if (name == QLatin1String("subdocument"))
        return FilterEngine::SubFrame;
    return 0;
}
}

void FilterEngine::addList(const QByteArray &text)
{
    const QList<QByteArray> lines = text.split('\n');
    for (const QByteArray &line : lines)
        addRule(QString::fromUtf8(line));
}

bool FilterEngine::addRule(const QString &input)
{
    QString line = input.trimmed();
    if (line.isEmpty() || line.startsWith(QLatin1Char('!')) || line.startsWith(QLatin1Char('[')))
        return false;
    // Cosmetic (element hiding) rules.
    if (line.contains(QLatin1String("##")) || line.contains(QLatin1String("#@#"))
        || line.contains(QLatin1String("#?#")) || line.contains(QLatin1String("#$#")))
        return false;

    Rule rule;
    if (line.startsWith(QLatin1String("@@"))) {
        rule.exception = true;
        line = line.mid(2);
    }

    // Options after the last '$'.
    const int dollar = line.lastIndexOf(QLatin1Char('$'));
    if (dollar >= 0) {
        const QStringList options = line.mid(dollar + 1).split(QLatin1Char(','));
        line = line.left(dollar);
        for (const QString &option : options) {
            const bool negated = option.startsWith(QLatin1Char('~'));
            const QString name = negated ? option.mid(1) : option;
            if (name == QLatin1String("third-party")) {
                rule.thirdParty = negated ? Rule::OnlyFirstParty : Rule::OnlyThirdParty;
            } else if (name.startsWith(QLatin1String("domain=")) && !negated) {
                const QStringList domains = name.mid(7).toLower().split(QLatin1Char('|'));
                for (const QString &domain : domains) {
                    if (domain.startsWith(QLatin1Char('~')))
                        rule.domainsExclude.append(domain.mid(1));
                    else if (!domain.isEmpty())
                        rule.domainsInclude.append(domain);
                }
            } else if (const int kind = kindForOption(name); kind != 0 && !negated) {
                rule.typeMask |= kind;
            } else {
                return false;   // unknown option: skip the rule
            }
        }
    }
    if (rule.typeMask == 0)
        rule.typeMask = SubFrame | Stylesheet | Script | Image | XmlHttpRequest | Other;

    // Regular expression rules are not supported.
    if (line.size() > 1 && line.startsWith(QLatin1Char('/')) && line.endsWith(QLatin1Char('/')))
        return false;

    line = line.toLower();
    bool domainAnchor = false;
    if (line.startsWith(QLatin1String("||"))) {
        domainAnchor = true;
        line = line.mid(2);
    } else if (line.startsWith(QLatin1Char('|'))) {
        rule.anchorStart = true;
        line = line.mid(1);
    }
    if (line.endsWith(QLatin1Char('|'))) {
        rule.anchorEnd = true;
        line.chop(1);
    }
    if (line.isEmpty())
        return false;

    if (domainAnchor) {
        int hostEnd = 0;
        while (hostEnd < line.size() && line.at(hostEnd) != QLatin1Char('^')
               && line.at(hostEnd) != QLatin1Char('/') && line.at(hostEnd) != QLatin1Char('*')
               && line.at(hostEnd) != QLatin1Char(':') && line.at(hostEnd) != QLatin1Char('?')
               && line.at(hostEnd) != QLatin1Char('|'))
            ++hostEnd;
        const QString host = line.left(hostEnd);
        if (host.isEmpty() || !host.contains(QLatin1Char('.')))
            return false;
        rule.pattern = line.mid(hostEnd);
        rule.anchorStart = true;    // the rest follows the host directly
        m_domainRules[host].append(rule);
    } else {
        rule.pattern = line;
        const QString token = tokenOf(line, rule.anchorStart, rule.anchorEnd);
        if (token.isEmpty())
            m_otherRules.append(rule);
        else
            m_tokenRules[token].append(rule);
    }
    ++m_ruleCount;
    return true;
}

bool FilterEngine::matchesPattern(const Rule &rule, const QString &text, bool unanchoredSearch)
{
    const QStringList segments = rule.pattern.split(QLatin1Char('*'));
    int pos = 0;
    for (int i = 0; i < segments.size(); ++i) {
        const QString &segment = segments.at(i);
        const bool first = i == 0;
        if (segment.isEmpty())
            continue;
        if (first && (rule.anchorStart || !unanchoredSearch)) {
            const int end = matchSegmentAt(segment, text, 0);
            if (end < 0)
                return false;
            pos = end;
        } else {
            int found = -1;
            int end = -1;
            for (int start = pos; start <= text.size(); ++start) {
                end = matchSegmentAt(segment, text, start);
                if (end >= 0) {
                    found = start;
                    break;
                }
            }
            if (found < 0)
                return false;
            pos = end;
        }
    }
    if (rule.anchorEnd && !rule.pattern.endsWith(QLatin1Char('*')))
        return pos == text.size();
    return true;
}

bool FilterEngine::optionsMatch(const Rule &rule, const Request &request)
{
    if (!(rule.typeMask & request.kind))
        return false;
    if (rule.thirdParty == Rule::OnlyThirdParty && !request.thirdParty)
        return false;
    if (rule.thirdParty == Rule::OnlyFirstParty && request.thirdParty)
        return false;
    if (!rule.domainsInclude.isEmpty() || !rule.domainsExclude.isEmpty()) {
        for (const QString &domain : rule.domainsExclude) {
            if (hostMatches(request.firstPartyHost, domain))
                return false;
        }
        if (!rule.domainsInclude.isEmpty()) {
            bool included = false;
            for (const QString &domain : rule.domainsInclude)
                included = included || hostMatches(request.firstPartyHost, domain);
            if (!included)
                return false;
        }
    }
    return true;
}

bool FilterEngine::matchesAny(const Request &request, bool exceptions) const
{
    // `||host` rules: the request host and each parent domain.
    QString host = request.host;
    while (!host.isEmpty()) {
        const auto it = m_domainRules.constFind(host);
        if (it != m_domainRules.constEnd()) {
            for (const Rule &rule : *it) {
                if (rule.exception != exceptions || !optionsMatch(rule, request))
                    continue;
                if (rule.pattern.isEmpty() || matchesPattern(rule, request.rest, false))
                    return true;
            }
        }
        const int dot = host.indexOf(QLatin1Char('.'));
        if (dot < 0)
            break;
        host = host.mid(dot + 1);
    }

    QSet<QString> seen;
    for (const QString &token : urlTokens(request.url)) {
        if (seen.contains(token))
            continue;
        seen.insert(token);
        const auto it = m_tokenRules.constFind(token);
        if (it == m_tokenRules.constEnd())
            continue;
        for (const Rule &rule : *it) {
            if (rule.exception == exceptions && optionsMatch(rule, request)
                && matchesPattern(rule, request.url, true))
                return true;
        }
    }
    for (const Rule &rule : m_otherRules) {
        if (rule.exception == exceptions && optionsMatch(rule, request)
            && matchesPattern(rule, request.url, true))
            return true;
    }
    return false;
}

bool FilterEngine::shouldBlock(const QUrl &url, const QString &firstPartyHost,
                               ResourceKind kind) const
{
    if (kind == MainFrame || m_ruleCount == 0)
        return false;
    const QString scheme = url.scheme();
    if (scheme != QLatin1String("http") && scheme != QLatin1String("https")
        && scheme != QLatin1String("ws") && scheme != QLatin1String("wss"))
        return false;

    Request request;
    request.url = url.toString(QUrl::FullyEncoded | QUrl::RemoveFragment).toLower();
    request.host = url.host().toLower();
    request.firstPartyHost = firstPartyHost.toLower();
    request.kind = kind;
    request.thirdParty = !request.firstPartyHost.isEmpty()
            && registrableDomain(request.host) != registrableDomain(request.firstPartyHost);
    const int hostStart = request.url.indexOf(QLatin1String("://")) + 3;
    const int hostPos = request.url.indexOf(request.host, hostStart);
    request.rest = hostPos < 0 ? QString() : request.url.mid(hostPos + request.host.size());

    return matchesAny(request, false) && !matchesAny(request, true);
}
