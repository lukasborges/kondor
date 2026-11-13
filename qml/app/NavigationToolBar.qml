import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ToolBar {
    id: root

    required property TabModel tabs
    required property var browserWindow

    readonly property alias downloadsPopup: downloadsList
    readonly property alias bookmarkEditor: addressBar.bookmarkEditor
    readonly property bool isLoading: tabs.currentTab ? tabs.currentTab.loading : false

    function focusAddressBar() {
        addressBar.focusAndSelectAll()
    }

    function clearAddressBar() {
        addressBar.text = ""
    }

    function reloadOrStop() {
        if (!tabs.currentTab)
            return
        if (isLoading)
            tabs.currentTab.stop()
        else
            tabs.currentTab.reload()
    }

    function goHome() {
        if (!tabs.currentTab)
            return
        if (Settings.homePage.trim().length === 0)
            tabs.currentTab.showNewTabPage()
        else
            tabs.currentTab.navigateTo(ProfileManager.resolveAddress(""))
    }

    Kirigami.Theme.colorSet: Kirigami.Theme.Window
    Kirigami.Theme.inherit: false

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 5
        anchors.rightMargin: 5
        spacing: 2

        ToolButton {
            display: AbstractButton.IconOnly
            icon.name: "go-previous"
            enabled: root.tabs.currentTab ? root.tabs.currentTab.canGoBack : false
            ToolTip.visible: hovered
            Accessible.name: ToolTip.text
            ToolTip.text: qsTr("Back")
            ToolTip.delay: 600
            onClicked: root.tabs.currentTab.goBack()
        }

        ToolButton {
            display: AbstractButton.IconOnly
            icon.name: "go-next"
            enabled: root.tabs.currentTab ? root.tabs.currentTab.canGoForward : false
            ToolTip.visible: hovered
            Accessible.name: ToolTip.text
            ToolTip.text: qsTr("Forward")
            ToolTip.delay: 600
            onClicked: root.tabs.currentTab.goForward()
        }

        ToolButton {
            display: AbstractButton.IconOnly
            icon.name: root.isLoading ? "process-stop" : "view-refresh"
            enabled: root.tabs.currentTab ? !root.tabs.currentTab.newTabPage : false
            ToolTip.visible: hovered
            Accessible.name: ToolTip.text
            ToolTip.text: root.isLoading ? qsTr("Stop") : qsTr("Reload")
            ToolTip.delay: 600
            onClicked: root.reloadOrStop()
        }

        ToolButton {
            display: AbstractButton.IconOnly
            icon.name: "go-home"
            ToolTip.visible: hovered
            Accessible.name: ToolTip.text
            ToolTip.text: qsTr("Home")
            ToolTip.delay: 600
            onClicked: root.goHome()
        }

        AddressBar {
            id: addressBar
            tabs: root.tabs
            browserWindow: root.browserWindow
        }

        ToolButton {
            id: downloadsButton
            visible: DownloadManager.model.count > 0
            display: AbstractButton.IconOnly
            icon.name: "download"
            ToolTip.visible: hovered
            Accessible.name: ToolTip.text
            ToolTip.text: qsTr("Downloads")
            ToolTip.delay: 600
            onClicked: downloadsList.opened ? downloadsList.close() : downloadsList.open()

            ProgressBar {
                anchors {
                    left: parent.left
                    right: parent.right
                    bottom: parent.bottom
                    margins: 4
                }
                height: 2
                visible: DownloadManager.hasActiveDownloads
                value: DownloadManager.activeProgress >= 0 ? DownloadManager.activeProgress : 0
                indeterminate: DownloadManager.activeProgress < 0
            }

            DownloadsPopup {
                id: downloadsList
                x: downloadsButton.width - width
                y: downloadsButton.height
            }
        }

        ToolButton {
            id: extensionsButton
            objectName: "extensionsButton"
            visible: root.tabs.currentTab !== null
                     && (ExtensionManager.revision,
                         ExtensionManager.hasActionExtensions(root.tabs.currentTab.isPrivate))
            display: AbstractButton.IconOnly
            icon.name: "plugins"
            ToolTip.visible: hovered
            Accessible.name: ToolTip.text
            ToolTip.text: qsTr("Extensions")
            ToolTip.delay: 600
            onClicked: extensionsMenu.popup(extensionsButton, 0, extensionsButton.height)

            ExtensionsMenu {
                id: extensionsMenu
                tab: root.tabs.currentTab
                onManageRequested: root.browserWindow.openSettingsPage("extensions")
            }
        }

        ToolButton {
            display: AbstractButton.IconOnly
            icon.name: "application-menu"
            ToolTip.visible: hovered
            Accessible.name: ToolTip.text
            ToolTip.text: qsTr("Menu")
            ToolTip.delay: 600
            onClicked: mainMenu.open()

            MainMenu {
                id: mainMenu
                browserWindow: root.browserWindow
            }
        }
    }
}
