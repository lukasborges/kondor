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
        }

        Item { Layout.fillHeight: true }
    }
}
