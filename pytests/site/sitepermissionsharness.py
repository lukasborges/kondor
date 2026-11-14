from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEnginePermission
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.tab import Tab

PermissionType = QWebEnginePermission.PermissionType
PermissionState = QWebEnginePermission.State


class PermissionFixture:
    def __init__(self) -> None:
        self.profile = QQuickWebEngineProfile()
        self.profile.setPersistentPermissionsPolicy(
            QQuickWebEngineProfile.PersistentPermissionsPolicy.StoreInMemory
        )
        self.tab = Tab(self.profile)

    def query(self, origin: QUrl, permission_type: PermissionType) -> QWebEnginePermission:
        return self.profile.queryPermission(origin, permission_type)

    def state_of(self, origin: QUrl, permission_type: PermissionType) -> PermissionState:
        return self.query(origin, permission_type).state()

    def geolocation_state(self, origin: QUrl) -> PermissionState:
        return self.state_of(origin, PermissionType.Geolocation)

    def enqueue(self, origin: QUrl, permission_type: PermissionType) -> None:
        self.tab.permissions.enqueue(self.query(origin, permission_type))

    def enqueue_geolocation(self, origin: QUrl) -> None:
        self.enqueue(origin, PermissionType.Geolocation)

    def has_pending(self) -> bool:
        return self.tab.permissions.pending is not None

    def pending_type(self) -> PermissionType:
        return self.tab.permissions.pending.permissionType()


def grant_geolocation(origin: QUrl) -> None:
    profile = ProfileManager.instance().defaultProfile()
    profile.queryPermission(origin, PermissionType.Geolocation).grant()
