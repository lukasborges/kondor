from dataclasses import dataclass, field
from typing import NamedTuple

from PySide6.QtCore import QDateTime, QUrl
from PySide6.QtSql import QSqlQuery

from kondor.core.database import sql
from kondor.core.settings.settings import Settings

TOP_SITES_WINDOW_MS = 90 * 24 * 60 * 60 * 1000
WWW_PREFIX = "www."
WEB_SCHEMES = ("http", "https")
RECENT_VISITS = (
    "SELECT url, title, visited_at FROM history WHERE visited_at >= ?"
    " ORDER BY visited_at DESC, id DESC"
)


@dataclass
class UrlStats:
    visits: int = 0
    last_visit: int = 0
    title: str = ""

    def rank(self) -> tuple[int, int]:
        return self.visits, self.last_visit


@dataclass
class HostStats:
    score: int = 0
    last_visit: int = 0
    urls: dict[str, UrlStats] = field(default_factory=dict)


class Visit(NamedTuple):
    host: str
    url: str
    title: str
    visited_at: int


class Tile(NamedTuple):
    host: str
    url: str
    title: str
    score: int
    last_visit: int


HostTable = dict[str, HostStats]


def host_without_www(url: QUrl) -> str:
    return str(url.host()).removeprefix(WWW_PREFIX)


def visit_of(row: QSqlQuery) -> Visit | None:
    url = QUrl(str(row.value(0)))
    host = host_without_www(url)
    if url.scheme() not in WEB_SCHEMES or not host:
        return None
    return Visit(host, url.toString(), str(row.value(1)), int(row.value(2)))


def accumulate(hosts: HostTable, visit: Visit) -> None:
    host_stats = hosts.setdefault(visit.host, HostStats())
    host_stats.score += 1
    host_stats.last_visit = max(host_stats.last_visit, visit.visited_at)
    url_stats = host_stats.urls.setdefault(visit.url, UrlStats())
    url_stats.visits += 1
    url_stats.last_visit = max(url_stats.last_visit, visit.visited_at)
    if not url_stats.title:
        url_stats.title = visit.title


def read_hosts() -> HostTable:
    hosts: HostTable = {}
    since = QDateTime.currentMSecsSinceEpoch() - TOP_SITES_WINDOW_MS
    rows = sql.run(RECENT_VISITS, (since,))
    while rows is not None and rows.next():
        visit = visit_of(rows)
        if visit is not None:
            accumulate(hosts, visit)
    return hosts


def tile_of(host: str, stats: HostStats) -> Tile:
    best_url = max(stats.urls, key=lambda url: stats.urls[url].rank())
    best = stats.urls[best_url]
    return Tile(host, best_url, best.title, stats.score, stats.last_visit)


def visible_tiles(hosts: HostTable) -> list[Tile]:
    hidden = Settings.instance().property("hiddenTopSites") or []
    return [tile_of(host, stats) for host, stats in hosts.items() if host not in hidden]


def sorted_by_relevance(tiles: list[Tile]) -> list[Tile]:
    return sorted(tiles, key=lambda tile: (tile.score, tile.last_visit), reverse=True)


def site_of(tile: Tile) -> dict[str, str]:
    return {"url": tile.url, "title": tile.title, "host": tile.host}


def top_sites(limit: int) -> list[dict[str, str]]:
    if limit <= 0:
        return []
    tiles = sorted_by_relevance(visible_tiles(read_hosts()))
    return [site_of(tile) for tile in tiles[:limit]]
