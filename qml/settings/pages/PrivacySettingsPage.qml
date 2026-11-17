import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ScrollView {
    id: root

    required property SettingsDraft draft
    property var sitePermissionsWindow: null

    contentWidth: availableWidth
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

    function openSitePermissions() {
        if (!root.sitePermissionsWindow)
            root.sitePermissionsWindow = sitePermissionsComponent.createObject(Window.window)
        root.sitePermissionsWindow.showWindow()
    }

    function describeAdBlockLists() {
        if (AdBlockManager.updating)
            return qsTr("Updating lists…")
        if (isNaN(AdBlockManager.lastUpdate.getTime()))
            return qsTr("Lists not downloaded yet")
        const updated = AdBlockManager.lastUpdate.toLocaleString(Qt.locale(), Locale.ShortFormat)
        return qsTr("Lists last updated: %1").arg(updated)
    }

    Component {
        id: sitePermissionsComponent
        SitePermissionsDialog {}
    }

    ColumnLayout {
        width: root.availableWidth
        spacing: Kirigami.Units.largeSpacing

        Kirigami.FormLayout {
            Layout.fillWidth: true

            CheckBox {
                id: cookiesCheck
                Kirigami.FormData.label: qsTr("Cookies:")
                text: qsTr("Block third-party cookies")
                onToggled: root.draft.blockThirdPartyCookies = checked
            }

            Binding {
                target: cookiesCheck
                property: "checked"
                value: root.draft.blockThirdPartyCookies
            }

            CheckBox {
                id: adBlockCheck
                Kirigami.FormData.label: qsTr("Ads and trackers:")
                text: qsTr("Block ads and trackers")
                onToggled: root.draft.adBlockEnabled = checked
            }

            Binding {
                target: adBlockCheck
                property: "checked"
                value: root.draft.adBlockEnabled
            }

            Label {
                text: root.describeAdBlockLists()
                color: Kirigami.Theme.disabledTextColor
            }

            CheckBox {
                id: clearOnExitCheck
                Kirigami.FormData.label: qsTr("On exit:")
                text: qsTr("Clear cookies, cache and history")
                onToggled: root.draft.clearDataOnExit = checked
            }

            Binding {
                target: clearOnExitCheck
                property: "checked"
                value: root.draft.clearDataOnExit
            }

            CheckBox {
                id: popupsCheck
                Kirigami.FormData.label: qsTr("Pop-ups:")
                text: qsTr("Block pop-ups that open without a click")
                onToggled: root.draft.blockPopups = checked
            }

            Binding {
                target: popupsCheck
                property: "checked"
                value: root.draft.blockPopups
            }

            Item { Kirigami.FormData.isSection: true }

            Button {
                Kirigami.FormData.label: qsTr("Browsing data:")
                text: qsTr("Clear Cookies and Cache Now")
                icon.name: "edit-clear-history"
                onClicked: ProfileManager.clearCookiesAndCacheNow()
            }

            Item { Kirigami.FormData.isSection: true }

            Button {
                Kirigami.FormData.label: qsTr("Site permissions:")
                text: qsTr("Manage Site Permissions…")
                icon.name: "security-high"
                onClicked: root.openSitePermissions()
            }

            Item { Kirigami.FormData.isSection: true }

            RemoteControlRestartMessage {
                Layout.fillWidth: true
            }

            CheckBox {
                id: remoteControlCheck
                Kirigami.FormData.label: qsTr("Remote control:")
                text: qsTr("Allow automation tools to control pages")
                onToggled: root.draft.remoteControlEnabled = checked
            }

            Binding {
                target: remoteControlCheck
                property: "checked"
                value: root.draft.remoteControlEnabled
            }

            Label {
                text: qsTr("Private browsing is unavailable while it is on.")
                color: Kirigami.Theme.disabledTextColor
            }

            SpinBox {
                id: remoteControlPortBox
                Kirigami.FormData.label: qsTr("Port:")
                from: 1024
                to: 65535
                editable: true
                enabled: root.draft.remoteControlEnabled
                textFromValue: function(value) { return String(value) }
                onValueModified: root.draft.remoteControlPort = value
            }

            Binding {
                target: remoteControlPortBox
                property: "value"
                value: root.draft.remoteControlPort
            }

            McpCommandRow {
                enabled: root.draft.remoteControlEnabled
                Kirigami.FormData.label: qsTr("MCP server:")
                Layout.fillWidth: true
            }

            Label {
                text: qsTr("Add it to an AI agent, such as Claude Code, as an MCP server.")
                color: Kirigami.Theme.disabledTextColor
            }
        }

        Item { Layout.fillHeight: true }
    }
}
