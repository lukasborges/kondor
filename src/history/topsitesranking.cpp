#include "history/topsitesranking.h"

#include "core/settings/settings.h"
#include "core/database/sql.h"

#include <QDateTime>
#include <QHash>
#include <QList>
#include <QUrl>
#include <QVariantMap>

#include <algorithm>
#include <iterator>

namespace TopSitesRanking {

namespace {

constexpr qint64 kTopSitesWindowMs = 90LL * 24 * 60 * 60 * 1000;

struct UrlStats {
    int visits = 0;
    qint64 lastVisit = 0;
    QString title;
};

struct HostStats {
    int score = 0;
    qint64 lastVisit = 0;
    QHash<QString, UrlStats> urls;
};

struct Visit {
    QString host;
    QString url;
    QString title;
    qint64 visitedAt = 0;
};

struct Tile {
    QString host;
    QString url;
    QString title;
    int score = 0;
    qint64 lastVisit = 0;
};

using HostTable = QHash<QString, HostStats>;

QString hostWithoutWww(const QUrl &url)
{
    QString host = url.host();
    if (host.startsWith(QLatin1String("www.")))
        host.remove(0, 4);
    return host;
}

bool isWebUrl(const QUrl &url)
{
    return url.scheme() == QLatin1String("http") || url.scheme() == QLatin1String("https");
}

std::optional<Visit> visitOf(QSqlQuery &row)
{
    const QUrl url(row.value(0).toString());
    const QString host = hostWithoutWww(url);
    if (!isWebUrl(url) || host.isEmpty())
        return std::nullopt;
    return Visit{host, url.toString(), row.value(1).toString(), row.value(2).toLongLong()};
}

void accumulate(HostTable &hosts, const Visit &visit)
{
    HostStats &hostStats = hosts[visit.host];
    ++hostStats.score;
    hostStats.lastVisit = qMax(hostStats.lastVisit, visit.visitedAt);
    UrlStats &urlStats = hostStats.urls[visit.url];
    ++urlStats.visits;
    urlStats.lastVisit = qMax(urlStats.lastVisit, visit.visitedAt);
    if (urlStats.title.isEmpty())
        urlStats.title = visit.title;
}

HostTable readHosts()
{
    HostTable hosts;
    auto rows = Sql::run(QStringLiteral(
        "SELECT url, title, visited_at FROM history WHERE visited_at >= ?"
        " ORDER BY visited_at DESC, id DESC"),
        {QDateTime::currentMSecsSinceEpoch() - kTopSitesWindowMs});
    while (rows && rows->next()) {
        if (const auto visit = visitOf(*rows))
            accumulate(hosts, *visit);
    }
    return hosts;
}

bool isBetterUrl(const UrlStats &candidate, const UrlStats &best)
{
    if (candidate.visits != best.visits)
        return candidate.visits > best.visits;
    return candidate.lastVisit > best.lastVisit;
}

Tile tileOf(const QString &host, const HostStats &stats)
{
    auto best = stats.urls.constBegin();
    for (auto it = std::next(best); it != stats.urls.constEnd(); ++it) {
        if (isBetterUrl(it.value(), best.value()))
            best = it;
    }
    return {host, best.key(), best.value().title, stats.score, stats.lastVisit};
}

QList<Tile> visibleTiles(const HostTable &hosts)
{
    const QStringList hidden = Settings::instance()->hiddenTopSites();
    QList<Tile> tiles;
    for (auto it = hosts.constBegin(); it != hosts.constEnd(); ++it) {
        if (!hidden.contains(it.key()))
            tiles.append(tileOf(it.key(), it.value()));
    }
    return tiles;
}

void sortByRelevance(QList<Tile> &tiles)
{
    std::sort(tiles.begin(), tiles.end(), [](const Tile &a, const Tile &b) {
        if (a.score != b.score)
            return a.score > b.score;
        return a.lastVisit > b.lastVisit;
    });
}

QVariantMap siteOf(const Tile &tile)
{
    return {
        {QStringLiteral("url"), tile.url},
        {QStringLiteral("title"), tile.title},
        {QStringLiteral("host"), tile.host},
    };
}

QVariantList firstSites(const QList<Tile> &tiles, int limit)
{
    QVariantList sites;
    const int count = qMin(limit, int(tiles.size()));
    for (int i = 0; i < count; ++i)
        sites.append(siteOf(tiles.at(i)));
    return sites;
}

}

QVariantList topSites(int limit)
{
    if (limit <= 0)
        return {};
    QList<Tile> tiles = visibleTiles(readHosts());
    sortByRelevance(tiles);
    return firstSites(tiles, limit);
}

}
