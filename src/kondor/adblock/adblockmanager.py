from PySide6.QtCore import Property, QDateTime, QObject, Signal, Slot
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.adblock import adblocksettings
from kondor.adblock.adblockallowlist import AdBlockAllowList
from kondor.adblock.adblockinterceptor import AdBlockInterceptor
from kondor.adblock.filters.filterengine import FilterEngine
from kondor.adblock.lists.filterlistdownloader import FilterListDownloader
from kondor.adblock.lists.filterlistloader import FilterListLoader
from kondor.adblock.lists.filterlists import (
    cached_filter_list_files,
    filter_cache_directory,
    is_cache_stale,
)


class AdBlockManager(QObject):
    enabledChanged = Signal()
    updatingChanged = Signal()
    lastUpdateChanged = Signal()
    blockedCountChanged = Signal(str)
    allowListChanged = Signal()
    _instance: "AdBlockManager | None" = None

    def __init__(self) -> None:
        super().__init__()
        self._interceptor = AdBlockInterceptor(self)
        self._downloader = FilterListDownloader(self)
        self._loader = FilterListLoader(self)
        self._allow_list = AdBlockAllowList()
        self._counts: dict[str, int] = {}
        self._reload_after_load = False
        self._interceptor.set_enabled(adblocksettings.is_enabled())
        self._sync_allowed_hosts()
        self._connect_parts()

    @classmethod
    def instance(cls) -> "AdBlockManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def cache_directory() -> str:
        return filter_cache_directory()

    def is_enabled(self) -> bool:
        return adblocksettings.is_enabled()

    def set_enabled(self, enabled: bool) -> None:
        adblocksettings.set_enabled(enabled)

    def is_updating(self) -> bool:
        return self._downloader.is_updating()

    def last_update(self) -> QDateTime:
        return adblocksettings.last_update()

    enabled = Property(bool, is_enabled, set_enabled, notify=enabledChanged)
    updating = Property(bool, is_updating, notify=updatingChanged)
    lastUpdate = Property(QDateTime, last_update, notify=lastUpdateChanged)

    def install(self, profile: QQuickWebEngineProfile) -> None:
        profile.setUrlRequestInterceptor(self._interceptor)

    def start(self) -> None:
        self._load_cached_lists()
        if is_cache_stale(self.last_update()):
            self.updateLists()

    def set_engine(self, engine: FilterEngine | None) -> None:
        self._interceptor.set_engine(engine)

    @Slot(str, result=bool)
    def isAllowed(self, host: str) -> bool:
        return self._allow_list.is_allowed(host)

    @Slot(str, bool)
    @Slot(str, bool, bool)
    def setAllowed(self, host: str, allowed: bool, persistent: bool = True) -> None:
        if not host:
            return
        if persistent:
            self._allow_list.set_persistent(host, allowed)
        else:
            self._allow_list.set_for_session(host, allowed)
        self._sync_allowed_hosts()
        self.allowListChanged.emit()

    @Slot(str, result=int)
    def blockedCount(self, host: str) -> int:
        return self._counts.get(host.lower(), 0)

    @Slot()
    def updateLists(self) -> None:
        self._downloader.update()

    def _connect_parts(self) -> None:
        adblocksettings.changed_signal(adblocksettings.ENABLED).connect(self._apply_enabled)
        adblocksettings.changed_signal(adblocksettings.ALLOW_LIST).connect(self._sync_allowed_hosts)
        adblocksettings.changed_signal(adblocksettings.LAST_UPDATE).connect(self.lastUpdateChanged)
        self._interceptor.blocked.connect(self._count_blocked)
        self._interceptor.pageStarted.connect(self._reset_count)
        self._loader.loaded.connect(self._use_loaded_engine)
        self._downloader.updatingChanged.connect(self.updatingChanged)
        self._downloader.finished.connect(self._update_last_update_and_reload)

    def _apply_enabled(self) -> None:
        self._interceptor.set_enabled(adblocksettings.is_enabled())
        self.enabledChanged.emit()

    def _sync_allowed_hosts(self) -> None:
        self._interceptor.set_allowed_hosts(self._allow_list.hosts())

    def _count_blocked(self, host: str) -> None:
        self._counts[host] = self._counts.get(host, 0) + 1
        self.blockedCountChanged.emit(host)

    def _reset_count(self, host: str) -> None:
        if self._counts.get(host, 0) == 0:
            return
        self._counts[host] = 0
        self.blockedCountChanged.emit(host)

    def _use_loaded_engine(self, engine: FilterEngine) -> None:
        self._interceptor.set_engine(engine)
        if not self._reload_after_load:
            return
        self._reload_after_load = False
        self._load_cached_lists()

    def _update_last_update_and_reload(self, is_any_list_current: bool) -> None:
        if not is_any_list_current:
            return
        adblocksettings.set_last_update(QDateTime.currentDateTime())
        self._load_cached_lists()

    def _load_cached_lists(self) -> None:
        if self._loader.is_running():
            self._reload_after_load = True
        else:
            self._loader.load(cached_filter_list_files())
