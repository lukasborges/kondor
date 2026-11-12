import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtWebEngine
import org.kde.kirigami as Kirigami
import Kondor

// Site information opened from the security indicator in the address bar:
// the connection state and the permissions the profile remembers for the site.
Popup {
    id: root

    property Tab tab: null
    property var permissions: []

    width: 360
    padding: Kirigami.Units.largeSpacing
    modal: false
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    readonly property string securityState: tab ? tab.securityState : ""

    function stateIcon() {
        switch (securityState) {
        case "secure":
            return "security-high"
        case "insecure":
            return "security-medium"
        case "error":
            return "security-low"
        }
        return "text-html"
    }

    function stateText() {
        switch (securityState) {
        case "secure":
            return qsTr("Connection is secure")
        case "insecure":
            return qsTr("Not Secure")
        case "error":
            return qsTr("Your connection is not private")
        }
        return qsTr("Local file")
    }

    function stateColor() {
        switch (securityState) {
        case "secure":
            return Kirigami.Theme.positiveTextColor
        case "insecure":
        case "error":
            return Kirigami.Theme.negativeTextColor
        }
        return Kirigami.Theme.disabledTextColor
    }

    function siteName() {
        if (!tab)
            return ""
        const text = tab.url.toString()
        const match = text.match(/^[a-z][a-z0-9+.-]*:\/\/([^\/?#]+)/i)
        return match ? match[1] : text
    }

    // Permissions are stored per origin (scheme + host + port).
    function originUrl() {
        if (!tab)
            return ""
        const match = tab.url.toString().match(/^(https?:\/\/[^\/?#]+)/i)
        return match ? match[1] : ""
    }

    function reload() {
        permissions = []
        const origin = originUrl()
        if (origin.length === 0)
            return

        const found = tab.profile.listPermissionsForOrigin(origin)
        let rows = []
        for (let i = 0; i < found.length; ++i) {
            const permission = found[i]
            if (!permission.isValid)
                continue
            if (permission.state !== WebEnginePermission.State.Granted
                    && permission.state !== WebEnginePermission.State.Denied)
                continue
            rows.push({
                icon: typeInfo.iconFor(permission.permissionType),
                label: typeInfo.labelFor(permission.permissionType),
                granted: permission.state === WebEnginePermission.State.Granted,
                permission: permission
            })
        }
        permissions = rows
    }

    function revoke(permission) {
        if (!permission || !permission.isValid)
            return
        permission.reset()
        reload()
        // The backend may apply the reset asynchronously; refresh once more.
        Qt.callLater(reload)
    }

    onOpened: reload()
    onTabChanged: {
        if (opened)
            reload()
    }

    PermissionTypeInfo {
        id: typeInfo
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        RowLayout {
            spacing: Kirigami.Units.largeSpacing

            Kirigami.Icon {
                source: root.stateIcon()
                Layout.preferredWidth: 32
                Layout.preferredHeight: 32
            }

            ColumnLayout {
                spacing: 0
                Layout.fillWidth: true

                Kirigami.Heading {
                    level: 4
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                    text: root.siteName()
                }

                Label {
                    Layout.fillWidth: true
                    text: root.stateText()
                    color: root.stateColor()
                }
            }
        }

        Kirigami.Separator {
            Layout.fillWidth: true
            visible: root.permissions.length > 0
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing
            visible: root.permissions.length > 0

            Label {
                text: qsTr("Permissions for this site")
                font.bold: true
            }

            Repeater {
                model: root.permissions

                delegate: RowLayout {
                    id: permissionRow
                    required property var modelData

                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing

                    Kirigami.Icon {
                        source: permissionRow.modelData.icon
                        Layout.preferredWidth: Kirigami.Units.iconSizes.small
                        Layout.preferredHeight: Kirigami.Units.iconSizes.small
                    }

                    Label {
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                        text: permissionRow.modelData.label
                    }

                    Label {
                        text: permissionRow.modelData.granted ? qsTr("Allowed") : qsTr("Blocked")
                        color: permissionRow.modelData.granted
                               ? Kirigami.Theme.positiveTextColor
                               : Kirigami.Theme.negativeTextColor
                    }

                    ToolButton {
                        display: AbstractButton.IconOnly
                        icon.name: "edit-undo"
                        ToolTip.visible: hovered
                        ToolTip.text: qsTr("Revoke")
                        ToolTip.delay: 600
                        onClicked: root.revoke(permissionRow.modelData.permission)
                    }
                }
            }
        }
    }
}
