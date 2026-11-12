pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtWebEngine
import org.kde.kirigami as Kirigami
import Kondor

ApplicationWindow {
    id: root
    width: 640
    height: 460
    minimumWidth: 480
    minimumHeight: 360
    //: %1 is the application name
    title: qsTr("Site Permissions — %1").arg(Qt.application.displayName)
    visible: false

    property var rows: []

    onClosing: function(close) {
        close.accepted = false
        root.visible = false
    }

    function showWindow() {
        filterField.text = ""
        root.reload()
        root.visible = true
        root.raise()
        root.requestActivate()
        filterField.forceActiveFocus()
    }

    function isDecided(permission) {
        return permission.isValid
            && (permission.state === WebEnginePermission.State.Granted
                || permission.state === WebEnginePermission.State.Denied)
    }

    function decidedPermissions() {
        return Array.from(ProfileManager.defaultProfile().listAllPermissions()).filter(isDecided)
    }

    function rowFor(permission) {
        return {
            site: typeInfo.hostFor(permission.origin),
            perm: typeInfo.labelFor(permission.permissionType),
            ic: typeInfo.iconFor(permission.permissionType),
            granted: permission.state === WebEnginePermission.State.Granted,
            permission: permission
        }
    }

    function compareRows(a, b) {
        if (a.site === b.site)
            return a.perm.localeCompare(b.perm)
        return a.site.localeCompare(b.site)
    }

    function matchesFilter(row) {
        const filter = filterField.text.trim().toLowerCase()
        return filter.length === 0 || row.site.toLowerCase().includes(filter)
    }

    function reload() {
        root.rows = decidedPermissions().map(rowFor).filter(matchesFilter).sort(compareRows)
    }

    function revoke(permission) {
        if (!permission || !permission.isValid)
            return
        permission.reset()
        root.reload()
        Qt.callLater(root.reload)
    }

    Shortcut {
        sequences: [StandardKey.Cancel]
        onActivated: root.visible = false
    }

    PermissionTypeInfo {
        id: typeInfo
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.largeSpacing

        Kirigami.Heading {
            level: 3
            text: qsTr("Site Permissions")
        }

        Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: Kirigami.Theme.disabledTextColor
            text: qsTr("Decisions remembered for sites visited in normal tabs. Private tabs never keep permissions.")
        }

        TextField {
            id: filterField
            Layout.fillWidth: true
            placeholderText: qsTr("Filter by site…")
            selectByMouse: true
            onTextChanged: root.reload()
        }

        Frame {
            Layout.fillWidth: true
            Layout.fillHeight: true
            padding: 0
            Kirigami.Theme.colorSet: Kirigami.Theme.View
            Kirigami.Theme.inherit: false
            background: Rectangle {
                color: Kirigami.Theme.backgroundColor
                border.color: Kirigami.ColorUtils.linearInterpolation(
                                  Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.2)
            }

            ListView {
                id: permissionList
                anchors.fill: parent
                clip: true
                model: root.rows
                section.property: "site"
                section.delegate: Kirigami.ListSectionHeader {
                    required property string section
                    width: ListView.view.width
                    text: section
                }

                delegate: ItemDelegate {
                    id: permissionDelegate

                    required property string perm
                    required property string ic
                    required property bool granted
                    required property var permission
                    width: ListView.view.width

                    contentItem: RowLayout {
                        spacing: Kirigami.Units.largeSpacing

                        Kirigami.Icon {
                            source: permissionDelegate.ic
                            Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                            Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                        }
                        Label {
                            text: permissionDelegate.perm
                            Layout.fillWidth: true
                        }
                        Label {
                            text: permissionDelegate.granted ? qsTr("Allowed") : qsTr("Blocked")
                            color: permissionDelegate.granted
                                   ? Kirigami.Theme.positiveTextColor
                                   : Kirigami.Theme.negativeTextColor
                        }
                        Button {
                            text: qsTr("Revoke")
                            icon.name: "edit-undo"
                            flat: true
                            onClicked: root.revoke(permissionDelegate.permission)
                        }
                    }
                }

                Label {
                    anchors.centerIn: parent
                    visible: root.rows.length === 0
                    color: Kirigami.Theme.disabledTextColor
                    text: qsTr("No site permissions have been remembered yet.")
                }
            }
        }

        DialogButtonBox {
            Layout.fillWidth: true
            padding: 0

            Button {
                text: qsTr("Close")
                icon.name: "dialog-close"
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
                onClicked: root.visible = false
            }
        }
    }
}
