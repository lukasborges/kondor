import QtQuick
import QtWebEngine
import Kondor

QtObject {
    id: root

    function isDecided(permission) {
        return permission.isValid
            && (permission.state === WebEnginePermission.State.Granted
                || permission.state === WebEnginePermission.State.Denied)
    }

    function rowFor(permission) {
        return {
            site: typeInfo.hostFor(permission.origin),
            perm: typeInfo.labelFor(permission.permissionType),
            ic: typeInfo.iconFor(permission.permissionType),
            granted: permission.state === WebEnginePermission.State.Granted,
            canRevoke: true,
            permission: permission
        }
    }

    function popupRow(host, canRevoke) {
        return {
            site: host,
            perm: qsTr("Pop-ups"),
            ic: "window-duplicate-symbolic",
            granted: true,
            canRevoke: canRevoke,
            permission: null
        }
    }

    function decidedRows(permissions) {
        return Array.from(permissions).filter(isDecided).map(rowFor)
    }

    function revoke(row) {
        if (!row.permission)
            SiteSettings.setPopupsAllowed(row.site, false)
        else if (row.permission.isValid)
            row.permission.reset()
    }

    property PermissionTypeInfo typeInfo: PermissionTypeInfo {}
}
