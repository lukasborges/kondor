pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// Native New Tab page shown by WebViewTab when its Tab is not displaying a
// page: the logo, a search field and the sites the user visits most. Private
// tabs get a variant without top sites and without touching the history.
Rectangle {
    id: page

    required property Tab tab
    required property TabModel tabModel

    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    color: Kirigami.Theme.backgroundColor

    property var topSites: []

    // The width available to the centered column, also used to decide how many
    // tiles fit per row. Using the grid's own width would create a binding loop
    // (columns -> implicit width -> columns).
    readonly property real contentWidth: Math.min(page.width - Kirigami.Units.gridUnit * 4,
                                                  Kirigami.Units.gridUnit
                                                  * (page.tab.isPrivate ? 30 : 36))

    function refreshTopSites() {
        if (page.tab.isPrivate || !Settings.showTopSites) {
            page.topSites = []
            return
        }
        page.topSites = HistoryManager.topSites(8)
    }

    function openInNewTab(url, isPrivate) {
        if (!url)
            return
        const profile = isPrivate ? ProfileManager.createPrivateProfile() : page.tab.profile
        page.tabModel.addTabWithProfile(profile, url, true)
    }

    function hideSite(host) {
        const hidden = Settings.hiddenTopSites.slice()
        if (hidden.indexOf(host) === -1)
            hidden.push(host)
        Settings.hiddenTopSites = hidden
    }

    onVisibleChanged: {
        if (visible)
            refreshTopSites()
    }
    Component.onCompleted: {
        if (visible)
            refreshTopSites()
    }

    Connections {
        target: Settings

        function onHiddenTopSitesChanged() {
            page.refreshTopSites()
        }
        function onShowTopSitesChanged() {
            page.refreshTopSites()
        }
    }

    ColumnLayout {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: Kirigami.Units.gridUnit * 4
        width: page.contentWidth
        spacing: Kirigami.Units.gridUnit * 2

        // ── Normal tab: logo and application name ───────────────────────
        RowLayout {
            visible: !page.tab.isPrivate
            Layout.alignment: Qt.AlignHCenter
            spacing: Kirigami.Units.largeSpacing

            Kirigami.Icon {
                source: "kondor"
                fallback: "internet-web-browser"
                Layout.preferredWidth: 64
                Layout.preferredHeight: 64
            }

            Kirigami.Heading {
                level: 1
                text: Qt.application.displayName
            }
        }

        // ── Private tab: icon and explanation ───────────────────────────
        Kirigami.Icon {
            visible: page.tab.isPrivate
            source: "view-private"
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 96
            Layout.preferredHeight: 96
        }

        Kirigami.Heading {
            visible: page.tab.isPrivate
            level: 1
            text: qsTr("Private Tab")
            Layout.alignment: Qt.AlignHCenter
        }

        TextField {
            id: addressField
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: Kirigami.Units.gridUnit * 30
            placeholderText: qsTr("Search or enter address")

            onAccepted: {
                if (text.trim().length === 0)
                    return
                page.tab.navigateTo(ProfileManager.resolveAddress(text))
                text = ""
            }
        }

        // ── Top sites (normal tabs only) ────────────────────────────────
        GridLayout {
            id: topSitesGrid
            Layout.alignment: Qt.AlignHCenter
            visible: !page.tab.isPrivate && Settings.showTopSites
                     && page.topSites.length > 0
            columns: Math.max(1, Math.min(4,
                Math.floor(page.contentWidth / (Kirigami.Units.gridUnit * 8))))
            rowSpacing: Kirigami.Units.largeSpacing
            columnSpacing: Kirigami.Units.largeSpacing

            Repeater {
                model: page.topSites

                delegate: ItemDelegate {
                    id: tile
                    required property var modelData

                    Layout.preferredWidth: Kirigami.Units.gridUnit * 7
                    Layout.maximumWidth: Kirigami.Units.gridUnit * 7
                    Accessible.name: tile.modelData.host

                    contentItem: ColumnLayout {
                        spacing: Kirigami.Units.smallSpacing

                        Rectangle {
                            Layout.alignment: Qt.AlignHCenter
                            Layout.preferredWidth: Kirigami.Units.gridUnit * 3.5
                            Layout.preferredHeight: Kirigami.Units.gridUnit * 3.5
                            radius: Kirigami.Units.cornerRadius
                            color: Kirigami.Theme.alternateBackgroundColor
                            border.color: Qt.alpha(Kirigami.Theme.textColor, 0.15)

                            Kirigami.Icon {
                                anchors.centerIn: parent
                                width: Kirigami.Units.iconSizes.medium
                                height: width
                                source: "image://favicon/" + tile.modelData.url
                                fallback: "internet-web-browser"
                            }
                        }

                        Label {
                            Layout.fillWidth: true
                            horizontalAlignment: Text.AlignHCenter
                            elide: Text.ElideRight
                            text: tile.modelData.host
                        }
                    }

                    ToolTip.visible: hovered
                    ToolTip.text: tile.modelData.title.length
                                  ? tile.modelData.title + "\n" + tile.modelData.url
                                  : tile.modelData.url
                    ToolTip.delay: 600

                    onClicked: {
                        if (BookmarkManager.ctrlPressed())
                            page.openInNewTab(tile.modelData.url, false)
                        else
                            page.tab.navigateTo(tile.modelData.url)
                    }

                    // The delegate only handles the left button.
                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.MiddleButton | Qt.RightButton
                        onClicked: function(mouse) {
                            if (mouse.button === Qt.MiddleButton) {
                                page.openInNewTab(tile.modelData.url, false)
                            } else {
                                tileMenu.site = tile.modelData
                                tileMenu.popup(tile, mouse.x, mouse.y)
                            }
                        }
                    }
                }
            }
        }

        Label {
            visible: !page.tab.isPrivate && Settings.showTopSites
                     && page.topSites.length === 0
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            color: Kirigami.Theme.disabledTextColor
            text: qsTr("The sites you visit most will appear here.")
        }

        Label {
            visible: page.tab.isPrivate
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            //: %1 is the application name
            text: qsTr("%1 does not keep the history, cookies, form data or permissions of this tab. Everything is erased when you close it.").arg(Qt.application.displayName)
        }

        Label {
            visible: page.tab.isPrivate
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            color: Kirigami.Theme.disabledTextColor
            text: qsTr("Downloads and bookmarks you create are kept. Your provider and the sites you visit can still see your activity.")
        }
    }

    Menu {
        id: tileMenu
        property var site: null

        MenuItem {
            text: qsTr("Open in New Tab")
            icon.name: "tab-new"
            onTriggered: {
                if (tileMenu.site)
                    page.openInNewTab(tileMenu.site.url, false)
            }
        }
        MenuItem {
            text: qsTr("Open in New Private Tab")
            icon.name: "view-private"
            onTriggered: {
                if (tileMenu.site)
                    page.openInNewTab(tileMenu.site.url, true)
            }
        }
        MenuSeparator {}
        MenuItem {
            text: qsTr("Remove from Top Sites")
            icon.name: "list-remove"
            onTriggered: {
                if (tileMenu.site)
                    page.hideSite(tileMenu.site.host)
            }
        }
    }
}
