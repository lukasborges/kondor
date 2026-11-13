#include "extensions/scripts/matchpatternglobs.h"

namespace {

QStringList schemesOf(const QString &scheme)
{
    if (scheme == QLatin1String("*"))
        return {QStringLiteral("http"), QStringLiteral("https")};
    return {scheme};
}

QStringList hostsOf(const QString &host)
{
    if (host == QLatin1String("*"))
        return {host};
    QStringList hosts{host};
    if (host.startsWith(QLatin1String("*.")))
        hosts.append(host.mid(2));
    for (const QString &name : QStringList(hosts))
        hosts.append(name + QStringLiteral(":*"));
    return hosts;
}

QString pathOf(const QString &matchPattern, int hostEnd)
{
    return matchPattern.mid(hostEnd);
}

QString hostPartOf(const QString &matchPattern, int schemeEnd, int hostEnd)
{
    return matchPattern.mid(schemeEnd + 3, hostEnd - schemeEnd - 3);
}

QStringList combine(const QStringList &schemes, const QStringList &hosts, const QString &path)
{
    QStringList globs;
    for (const QString &scheme : schemes) {
        for (const QString &host : hosts)
            globs.append(scheme + QStringLiteral("://") + host + path);
    }
    return globs;
}

}

QStringList matchPatternAsGlobs(const QString &matchPattern)
{
    if (matchPattern == QLatin1String("<all_urls>"))
        return {QStringLiteral("*")};
    const int schemeEnd = matchPattern.indexOf(QLatin1String("://"));
    const int hostEnd = matchPattern.indexOf(QLatin1Char('/'), schemeEnd + 3);
    if (schemeEnd < 0 || hostEnd < 0)
        return {matchPattern};
    return combine(schemesOf(matchPattern.left(schemeEnd)),
                   hostsOf(hostPartOf(matchPattern, schemeEnd, hostEnd)),
                   pathOf(matchPattern, hostEnd));
}
