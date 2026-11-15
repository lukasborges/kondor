from PySide6.QtCore import QDate, QDateTime, QTime, QUrl
from PySide6.QtSql import QSqlQuery

from kondor.core.database import sql

HOST_COMPLETION_CANDIDATES = 50
WWW_PREFIX = "www."
MATCHING_VISITS = (
    "SELECT url, title, COUNT(*) AS visits, MAX(visited_at) AS last"
    " FROM history WHERE url LIKE ? ESCAPE '\\' OR title LIKE ? ESCAPE '\\'"
    " GROUP BY url ORDER BY visits DESC, last DESC LIMIT ?"
)
RECENT_TODAY = (
    "SELECT url, title, MAX(visited_at) AS last FROM history WHERE visited_at >= ?"
    " GROUP BY url ORDER BY last DESC LIMIT ?"
)


def like_pattern(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def suggestion_of(query: QSqlQuery) -> dict[str, str]:
    return {"type": "history", "url": str(query.value(0)), "title": str(query.value(1))}


def recent_entry_of(query: QSqlQuery) -> dict[str, str]:
    return {"url": str(query.value(0)), "title": str(query.value(1))}


def host_without_www(suggestion: dict[str, str]) -> str:
    host = str(QUrl(suggestion["url"]).host())
    return host.removeprefix(WWW_PREFIX)


def starts_with_ignoring_case(text: str, prefix: str) -> bool:
    return text[: len(prefix)].casefold() == prefix.casefold()


def completes_prefix(host: str, prefix: str) -> bool:
    return len(host) > len(prefix) and starts_with_ignoring_case(host, prefix)


def matching_visits(needle: str, limit: int) -> QSqlQuery | None:
    pattern = like_pattern(needle)
    return sql.run(MATCHING_VISITS, (pattern, pattern, limit))


def local_midnight() -> int:
    return int(QDateTime(QDate.currentDate(), QTime(0, 0)).toMSecsSinceEpoch())


def suggest(text: str, limit: int) -> list[dict[str, str]]:
    needle = text.strip()
    if not needle or limit <= 0:
        return []
    query = matching_visits(needle, limit)
    suggestions = []
    while query is not None and query.next():
        suggestions.append(suggestion_of(query))
    return suggestions


def recent_today(limit: int) -> list[dict[str, str]]:
    if limit <= 0:
        return []
    query = sql.run(RECENT_TODAY, (local_midnight(), limit))
    entries = []
    while query is not None and query.next():
        entries.append(recent_entry_of(query))
    return entries


def host_completion(text: str) -> str:
    prefix = text.strip()
    if not prefix or " " in prefix:
        return ""
    hosts = (host_without_www(item) for item in suggest(prefix, HOST_COMPLETION_CANDIDATES))
    return next((host for host in hosts if completes_prefix(host, prefix)), "")
