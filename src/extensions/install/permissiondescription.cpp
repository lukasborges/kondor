#include "extensions/install/permissiondescription.h"

#include <QCoreApplication>
#include <QVariantMap>

#include <optional>

namespace PermissionDescription {

namespace {

struct PermissionLine {
    const char *permission;
    const char *icon;
    const char *text;
};

const PermissionLine kPermissionLines[] = {
    {"tabs", "tab-new",
     QT_TRANSLATE_NOOP("ExtensionPackage", "Open, close and navigate your tabs")},
    {"downloads", "download", QT_TRANSLATE_NOOP("ExtensionPackage", "Download files")},
    {"notifications", "notifications",
     QT_TRANSLATE_NOOP("ExtensionPackage", "Show notifications")},
};

struct SiteAccess {
    bool isAll = false;
    QStringList hosts;
};

QVariantMap entryOf(const QString &icon, const QString &text)
{
    return QVariantMap{{QStringLiteral("icon"), icon}, {QStringLiteral("text"), text}};
}

bool isHttpOrWildcardScheme(const QString &scheme)
{
    return scheme == QLatin1String("*") || scheme == QLatin1String("http")
        || scheme == QLatin1String("https");
}

bool grantsAllSites(const PatternParts &parts)
{
    return parts.all || (isHttpOrWildcardScheme(parts.scheme) && parts.host == QLatin1String("*"));
}

SiteAccess summarizeSites(const QStringList &matches)
{
    SiteAccess access;
    for (const QString &match : matches) {
        const PatternParts parts = parsePattern(match);
        access.isAll = grantsAllSites(parts);
        if (access.isAll)
            return access;
        if (!parts.host.isEmpty() && !access.hosts.contains(parts.host))
            access.hosts.append(parts.host);
    }
    return access;
}

QString hostList(const QStringList &hosts)
{
    const QString list = hosts.mid(0, 3).join(QStringLiteral(", "));
    if (hosts.size() <= 3)
        return list;
    //: %1 is a list of sites, %n the number of further sites
    return QCoreApplication::translate("ExtensionPackage", "%1 and %n more", nullptr,
                                       int(hosts.size() - 3)).arg(list);
}

std::optional<QVariantMap> siteAccessEntry(const QStringList &matches)
{
    const QString icon = QStringLiteral("internet-services");
    const SiteAccess access = summarizeSites(matches);
    if (access.isAll)
        return entryOf(icon, QCoreApplication::translate("ExtensionPackage",
                                                         "Read and change all websites"));
    if (access.hosts.isEmpty())
        return std::nullopt;
    return entryOf(icon, QCoreApplication::translate("ExtensionPackage",
                                                     "Read and change pages on %1")
                             .arg(hostList(access.hosts)));
}

}

PatternParts parsePattern(const QString &pattern)
{
    PatternParts parts;
    parts.all = pattern == QLatin1String("<all_urls>");
    const int schemeEnd = pattern.indexOf(QLatin1String("://"));
    if (parts.all || schemeEnd < 0)
        return parts;
    parts.scheme = pattern.left(schemeEnd);
    const int hostStart = schemeEnd + 3;
    const int hostEnd = pattern.indexOf(QLatin1Char('/'), hostStart);
    parts.host = pattern.mid(hostStart, hostEnd < 0 ? -1 : hostEnd - hostStart);
    return parts;
}

QVariantList permissionEntries(const QStringList &matches, const QStringList &permissions)
{
    QVariantList entries;
    if (const auto site = siteAccessEntry(matches))
        entries.append(*site);
    for (const PermissionLine &line : kPermissionLines) {
        if (permissions.contains(QLatin1String(line.permission)))
            entries.append(entryOf(QLatin1String(line.icon),
                                   QCoreApplication::translate("ExtensionPackage", line.text)));
    }
    return entries;
}

QStringList permissionLines(const QStringList &matches, const QStringList &permissions)
{
    QStringList lines;
    const QVariantList entries = permissionEntries(matches, permissions);
    for (const QVariant &entry : entries)
        lines.append(entry.toMap().value(QStringLiteral("text")).toString());
    return lines;
}

}
