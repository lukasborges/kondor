from typing import ClassVar

import shiboken6
from PySide6.QtCore import Property, QObject, Signal, Slot

from kondor.profiles import profilelauncher
from kondor.profiles.activeprofile import ActiveProfile
from kondor.profiles.profileremoval import remove_profile_data
from kondor.profiles.registry.profileregistry import ProfileRegistry
from kondor.profiles.registry.registrywatcher import RegistryWatcher
from kondor.profiles.userprofile import ASK_EVERY_TIME, DEFAULT_ID, PROFILE_ICONS, UserProfile


class UserProfiles(QObject):
    profilesChanged = Signal()
    startupProfileIdChanged = Signal()
    manageWindowChanged = Signal()
    _instance: ClassVar["UserProfiles | None"] = None

    def __init__(self) -> None:
        super().__init__()
        self._registry = ProfileRegistry()
        self._profiles = self._registry.profiles()
        self._startup_id = self._registry.startup_profile_id()
        self._manage_window: QObject | None = None
        self._watcher = RegistryWatcher(self)
        self._watcher.changed.connect(self.reload)

    @classmethod
    def instance(cls) -> "UserProfiles":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @Slot()
    def reload(self) -> None:
        profiles = self._registry.profiles()
        if profiles != self._profiles:
            self._profiles = profiles
            self.profilesChanged.emit()
        self._reload_startup_id()

    def _reload_startup_id(self) -> None:
        startup_id = self._registry.startup_profile_id()
        if startup_id != self._startup_id:
            self._startup_id = startup_id
            self.startupProfileIdChanged.emit()

    def profile_maps(self) -> list[dict[str, str]]:
        return [profile.as_map() for profile in self._profiles]

    def current_profile(self) -> UserProfile:
        found = self._registry.find(ActiveProfile.id())
        return found if found is not None else UserProfile(DEFAULT_ID, "", PROFILE_ICONS[0])

    def current_id(self) -> str:
        return ActiveProfile.id()

    def current_name(self) -> str:
        return self.current_profile().name

    def current_icon_name(self) -> str:
        return self.current_profile().icon_name

    def has_several_profiles(self) -> bool:
        return len(self._profiles) > 1

    def startup_profile_id(self) -> str:
        return "" if self._startup_id == ASK_EVERY_TIME else self._startup_id

    def set_startup_profile_id(self, value: str) -> None:
        self._registry.set_startup_profile_id(value or ASK_EVERY_TIME)
        self.reload()

    profiles = Property("QVariantList", profile_maps, notify=profilesChanged)
    currentId = Property(str, current_id, constant=True)
    currentName = Property(str, current_name, notify=profilesChanged)
    currentIconName = Property(str, current_icon_name, notify=profilesChanged)
    hasSeveralProfiles = Property(bool, has_several_profiles, notify=profilesChanged)
    startupProfileId = Property(
        str, startup_profile_id, set_startup_profile_id, notify=startupProfileIdChanged
    )

    def last_used_profile_id(self) -> str:
        return self._registry.last_used_id()

    lastUsedProfileId = Property(str, last_used_profile_id, constant=True)

    def manage_window(self) -> QObject | None:
        window = self._manage_window
        return window if window is not None and shiboken6.isValid(window) else None

    def set_manage_window(self, window: QObject | None) -> None:
        self._manage_window = window
        self.manageWindowChanged.emit()

    manageWindow = Property(QObject, manage_window, set_manage_window, notify=manageWindowChanged)

    @Slot(str)
    def openWindow(self, profile_id: str) -> None:
        profilelauncher.open_profile_window(profile_id)

    @Slot(str, str, result=str)
    def createProfile(self, name: str, icon_name: str) -> str:
        profile = self._registry.add(name, icon_name)
        self.reload()
        return profile.id

    @Slot(str, str, str)
    def editProfile(self, profile_id: str, name: str, icon_name: str) -> None:
        self._registry.update(UserProfile(profile_id, name, icon_name))
        self.reload()

    @Slot(str, result=bool)
    def deleteProfile(self, profile_id: str) -> bool:
        if profile_id == DEFAULT_ID or self.isRunning(profile_id):
            return False
        removed = remove_profile_data(profile_id)
        self._registry.remove(profile_id)
        self.reload()
        return removed

    @Slot(str, str, result=str)
    def nameError(self, name: str, except_id: str) -> str:
        return self._registry.name_error(name, except_id)

    @Slot(str, result=bool)
    def isRunning(self, profile_id: str) -> bool:
        return profilelauncher.is_running(profile_id)

    @Slot(result="QStringList")
    def iconNames(self) -> list[str]:
        return list(PROFILE_ICONS)
