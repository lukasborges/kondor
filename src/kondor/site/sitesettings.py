from PySide6.QtCore import QObject, Signal, Slot

from kondor.core.database import sql

SELECT_ALLOWED = "SELECT allow_popups FROM site_settings WHERE host = ?"
SELECT_ALLOWED_HOSTS = "SELECT host FROM site_settings WHERE allow_popups = 1 ORDER BY host"
UPSERT_ALLOWED = (
    "INSERT INTO site_settings (host, allow_popups) VALUES (?, ?) "
    "ON CONFLICT(host) DO UPDATE SET allow_popups = excluded.allow_popups"
)
DELETE_EMPTY_ROW = (
    "DELETE FROM site_settings WHERE host = ? AND allow_popups = 0 AND user_agent IS NULL"
)


class SiteSettings(QObject):
    changed = Signal(str)
    _instance: "SiteSettings | None" = None

    @classmethod
    def instance(cls) -> "SiteSettings":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @Slot(str, result=bool)
    def popupsAllowed(self, host: str) -> bool:
        query = sql.run(SELECT_ALLOWED, (host.lower(),))
        return query is not None and query.next() and bool(query.value(0))

    @Slot(str, bool)
    def setPopupsAllowed(self, host: str, allowed: bool) -> None:
        key = host.lower()
        if not key or self.popupsAllowed(key) == allowed:
            return
        sql.run(UPSERT_ALLOWED, (key, 1 if allowed else 0))
        sql.run(DELETE_EMPTY_ROW, (key,))
        self.changed.emit(key)

    @Slot(result="QStringList")
    def hostsWithPopupsAllowed(self) -> list[str]:
        query = sql.run(SELECT_ALLOWED_HOSTS)
        hosts: list[str] = []
        while query is not None and query.next():
            hosts.append(str(query.value(0)))
        return hosts
