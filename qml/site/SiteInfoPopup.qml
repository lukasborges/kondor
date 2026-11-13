import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtWebEngine
import org.kde.kirigami as Kirigami
import Kondor

Popup {
    id: root

    property Tab tab: null
    property var permissions: []

    width: 360
    padding: Kirigami.Units.largeSpacing
    modal: false
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    function isDecided(permission) {
        return permission.isValid
            && (permission.state === WebEnginePermission.State.Granted
                || permission.state === WebEnginePermission.State.Denied)
    }

    function rowFor(permission) {
        return {
            icon: typeInfo.iconFor(permission.permissionType),
            label: typeInfo.labelFor(permission.permissionType),
            granted: permission.state === WebEnginePermission.State.Granted,
            permission: permission
        }
    }

    function decidedPermissions(origin) {
        return Array.from(tab.profile.listPermissionsForOrigin(origin)).filter(isDecided)
    }

    function reload() {
        const origin = security.originUrl()
        permissions = origin.length === 0 ? [] : decidedPermissions(origin).map(rowFor)
    }

    function revoke(permission) {
        if (!permission || !permission.isValid)
            return
        permission.reset()
        reload()
        Qt.callLater(reload)
    }

    onOpened: reload()
    onTabChanged: {
        if (opened)
            reload()
    }

    SiteSecurityState {
        id: security
        tab: root.tab
    }

    PermissionTypeInfo {
        id: typeInfo
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        RowLayout {
            spacing: Kirigami.Units.largeSpacing

            Kirigami.Icon {
                source: security.stateIcon
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
                    text: security.siteName()
                }

                Label {
                    Layout.fillWidth: true
                    text: security.stateText
                    color: security.stateColor
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
                        Accessible.name: ToolTip.text
                        ToolTip.text: qsTr("Revoke")
                        ToolTip.delay: 600
                        onClicked: root.revoke(permissionRow.modelData.permission)
                    }
                }
            }
        }
    }
}
