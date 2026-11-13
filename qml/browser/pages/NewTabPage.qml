pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Rectangle {
    id: page

    required property Tab tab
    required property TabModel tabModel

    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    color: Kirigami.Theme.backgroundColor

    property var topSites: []

    readonly property real contentWidth: Math.min(page.width - Kirigami.Units.gridUnit * 4,
                                                  Kirigami.Units.gridUnit
                                                  * (page.tab.isPrivate ? 30 : 36))
    readonly property bool showsTopSites: !page.tab.isPrivate && Settings.showTopSites

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

    function search(text) {
        if (text.trim().length === 0)
            return false
        page.tab.navigateTo(ProfileManager.resolveAddress(text))
        return true
    }

    function refreshIfVisible() {
        if (visible)
            refreshTopSites()
    }

    onVisibleChanged: refreshIfVisible()
    Component.onCompleted: refreshIfVisible()

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

            onAccepted: if (page.search(text)) text = ""
        }

        TopSitesGrid {
            Layout.alignment: Qt.AlignHCenter
            visible: page.showsTopSites && page.topSites.length > 0
            sites: page.topSites
            contentWidth: page.contentWidth
            onNavigateRequested: function(url) { page.tab.navigateTo(url) }
            onOpenInNewTabRequested: function(url) { page.openInNewTab(url, false) }
            onMenuRequested: function(request) { tileMenu.popupFor(request) }
        }

        Label {
            visible: page.showsTopSites && page.topSites.length === 0
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

    TopSiteMenu {
        id: tileMenu
        onOpenRequested: function(url, isPrivate) { page.openInNewTab(url, isPrivate) }
        onHideRequested: function(host) { page.hideSite(host) }
    }
}
