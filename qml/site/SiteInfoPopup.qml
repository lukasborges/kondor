import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtWebEngine
import org.kde.kirigami as Kirigami
import Kondor

ToolbarPopup {
    id: root

    property Tab tab: null
    property var permissions: []

    width: 360
    padding: Kirigami.Units.largeSpacing

    readonly property bool hasSiteSettings: tab !== null && tab.identity.host.length > 0
    readonly property bool hasSection: permissions.length > 0 || hasSiteSettings

    function popupRows() {
        if (!tab.popups.isAllowed)
            return []
        return [permissionRows.popupRow(tab.popups.host, tab.popups.canChangeAllowed)]
    }

    function decidedRows(origin) {
        if (origin.length === 0)
            return []
        return permissionRows.decidedRows(tab.profile.listPermissionsForOrigin(origin))
    }

    function reload() {
        permissions = decidedRows(security.originUrl()).concat(popupRows())
    }

    function revoke(row) {
        permissionRows.revoke(row)
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

    PermissionRows {
        id: permissionRows
    }

    CustomIdentityDialog {
        id: customIdentityDialog
        identity: root.tab ? root.tab.identity : null
        onClosed: identityRow.syncChoice()
    }

    Connections {
        target: root.tab ? root.tab.popups : null
        function onAllowedChanged() {
            if (root.opened)
                root.reload()
        }
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
            visible: root.hasSection
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing
            visible: root.hasSection

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
                        source: permissionRow.modelData.iconName
                        Layout.preferredWidth: Kirigami.Units.iconSizes.small
                        Layout.preferredHeight: Kirigami.Units.iconSizes.small
                    }

                    Label {
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                        text: permissionRow.modelData.label
                    }

                    Label {
                        visible: permissionRow.modelData.showsState
                        text: permissionRow.modelData.granted ? qsTr("Allowed") : qsTr("Blocked")
                        color: permissionRow.modelData.granted
                               ? Kirigami.Theme.positiveTextColor
                               : Kirigami.Theme.negativeTextColor
                    }

                    ToolButton {
                        visible: permissionRow.modelData.canRevoke
                        display: AbstractButton.IconOnly
                        icon.name: "edit-undo"
                        ToolTip.visible: hovered
                        Accessible.name: ToolTip.text
                        ToolTip.text: qsTr("Revoke")
                        ToolTip.delay: 600
                        onClicked: root.revoke(permissionRow.modelData)
                    }
                }
            }

            IdentityRow {
                id: identityRow
                Layout.fillWidth: true
                visible: root.hasSiteSettings
                identity: root.tab ? root.tab.identity : null
                onCustomRequested: customIdentityDialog.open()
            }
        }
    }
}
