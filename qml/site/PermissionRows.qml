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
            label: typeInfo.labelFor(permission.permissionType),
            iconName: typeInfo.iconFor(permission.permissionType),
            granted: permission.state === WebEnginePermission.State.Granted,
            canRevoke: true,
            showsState: true,
            permission: permission
        }
    }

    function popupRow(host, canRevoke) {
        return {
            site: host,
            label: qsTr("Pop-ups"),
            iconName: "window-duplicate-symbolic",
            granted: true,
            canRevoke: canRevoke,
            showsState: true,
            permission: null
        }
    }

    function identityLabel(agent) {
        const name = identityChoices.nameOf(BrowserIdentity.choiceOf(agent))
        //: %1 is the browser the site is told Kondor is, such as Firefox
        return qsTr("Browser identity — %1").arg(name)
    }

    function identityRow(host, agent) {
        return {
            site: host,
            label: identityLabel(agent),
            iconName: "preferences-web-browser-identification",
            granted: true,
            canRevoke: true,
            showsState: false,
            permission: null,
            identityHost: host
        }
    }

    function identityRows() {
        const hosts = SiteSettings.hostsWithUserAgent()
        return hosts.map(host => identityRow(host, SiteSettings.userAgent(host)))
    }

    function decidedRows(permissions) {
        return Array.from(permissions).filter(isDecided).map(rowFor)
    }

    function revoke(row) {
        if (row.identityHost)
            SiteSettings.setUserAgent(row.identityHost, "")
        else if (!row.permission)
            SiteSettings.setPopupsAllowed(row.site, false)
        else if (row.permission.isValid)
            row.permission.reset()
    }

    property IdentityChoices identityChoices: IdentityChoices {}
    property PermissionTypeInfo typeInfo: PermissionTypeInfo {}
}
