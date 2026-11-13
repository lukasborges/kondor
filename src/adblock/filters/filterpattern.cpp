#include "adblock/filters/filterpattern.h"

namespace {
constexpr int kMinTokenLength = 3;

struct Run {
    int start;
    int end;
    int length() const { return end - start; }
};

bool isAlnum(QChar c)
{
    return (c >= QLatin1Char('a') && c <= QLatin1Char('z'))
            || (c >= QLatin1Char('0') && c <= QLatin1Char('9'));
}

bool isSeparator(QChar c)
{
    return !(isAlnum(c) || QStringLiteral("_-.%").contains(c));
}

int endOfRun(const QString &text, int start)
{
    int end = start;
    while (end < text.size() && isAlnum(text.at(end)))
        ++end;
    return end;
}

QList<Run> alnumRuns(const QString &text)
{
    QList<Run> runs;
    int i = 0;
    while (i < text.size()) {
        const int end = endOfRun(text, i);
        if (end > i)
            runs.append({i, end});
        i = end + 1;
    }
    return runs;
}

int advanceOverSeparator(const QString &text, int position)
{
    if (position == text.size())
        return position;
    return isSeparator(text.at(position)) ? position + 1 : -1;
}

int advance(QChar expected, const QString &text, int position)
{
    if (expected == QLatin1Char('^'))
        return advanceOverSeparator(text, position);
    if (position >= text.size() || text.at(position) != expected)
        return -1;
    return position + 1;
}

int searchSegment(const QString &segment, const QString &text, int from)
{
    for (int start = from; start <= text.size(); ++start) {
        const int end = matchSegmentAt(segment, text, start);
        if (end >= 0)
            return end;
    }
    return -1;
}

bool endsWhereRequired(const FilterRule &rule, const QString &text, int position)
{
    const bool mustEndAtEnd = rule.anchorEnd && !rule.pattern.endsWith(QLatin1Char('*'));
    return !mustEndAtEnd || position == text.size();
}

bool isLeftBound(const QString &pattern, const Run &run, bool anchorStart)
{
    return run.start > 0 ? pattern.at(run.start - 1) != QLatin1Char('*') : anchorStart;
}

bool isRightBound(const QString &pattern, const Run &run, bool anchorEnd)
{
    return run.end < pattern.size() ? pattern.at(run.end) != QLatin1Char('*') : anchorEnd;
}

bool hasShortSecondLevelUnderCountryCode(const QStringList &labels)
{
    return labels.size() >= 3 && labels.last().size() == 2
            && labels.at(labels.size() - 2).size() <= 3;
}
}

int matchSegmentAt(const QString &segment, const QString &text, int position)
{
    for (const QChar expected : segment) {
        position = advance(expected, text, position);
        if (position < 0)
            return -1;
    }
    return position;
}

bool matchesPattern(const FilterRule &rule, const QString &text, bool isUnanchoredSearch)
{
    const QStringList segments = rule.pattern.split(QLatin1Char('*'));
    const bool isFirstAnchored = rule.anchorStart || !isUnanchoredSearch;
    int position = 0;
    for (int i = 0; i < segments.size() && position >= 0; ++i) {
        if (segments.at(i).isEmpty())
            continue;
        position = i == 0 && isFirstAnchored ? matchSegmentAt(segments.at(i), text, 0)
                                             : searchSegment(segments.at(i), text, position);
    }
    return position >= 0 && endsWhereRequired(rule, text, position);
}

QString tokenOf(const QString &pattern, bool anchorStart, bool anchorEnd)
{
    QString best;
    for (const Run &run : alnumRuns(pattern)) {
        if (run.length() < kMinTokenLength || run.length() <= best.size())
            continue;
        if (isLeftBound(pattern, run, anchorStart) && isRightBound(pattern, run, anchorEnd))
            best = pattern.mid(run.start, run.length());
    }
    return best;
}

QSet<QString> urlTokens(const QString &url)
{
    QSet<QString> tokens;
    for (const Run &run : alnumRuns(url)) {
        if (run.length() >= kMinTokenLength)
            tokens.insert(url.mid(run.start, run.length()));
    }
    return tokens;
}

QString registrableDomain(const QString &host)
{
    const QStringList labels = host.split(QLatin1Char('.'));
    const int keep = hasShortSecondLevelUnderCountryCode(labels) ? 3 : 2;
    if (labels.size() <= keep)
        return host;
    return labels.mid(labels.size() - keep).join(QLatin1Char('.'));
}

bool hostMatches(const QString &host, const QString &domain)
{
    return host == domain || host.endsWith(QLatin1Char('.') + domain);
}

namespace {
QString textAfterHost(const FilterRequest &request)
{
    const int hostStart = request.url.indexOf(QLatin1String("://")) + 3;
    const int hostPosition = request.url.indexOf(request.host, hostStart);
    if (hostPosition < 0)
        return QString();
    return request.url.mid(hostPosition + request.host.size());
}
}

FilterRequest makeFilterRequest(const QUrl &url, const QString &firstPartyHost,
                                FilterEngine::ResourceKind kind)
{
    FilterRequest request;
    request.url = url.toString(QUrl::FullyEncoded | QUrl::RemoveFragment).toLower();
    request.host = url.host().toLower();
    request.firstPartyHost = firstPartyHost.toLower();
    request.kind = kind;
    request.thirdParty = !request.firstPartyHost.isEmpty()
            && registrableDomain(request.host) != registrableDomain(request.firstPartyHost);
    request.rest = textAfterHost(request);
    return request;
}
