import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Popup {
    id: root

    required property var tab
    required property var browserWindow

    property var folderPath: []

    readonly property bool isInFolder: content.folderId > 0
    readonly property bool isRightToLeft: Qt.application.layoutDirection === Qt.RightToLeft
    readonly property var folderBookmarks: content.entries.filter(function(entry) { return !entry.isFolder })

    function resetLevel() {
        folderPath = []
        search.clear()
    }

    function enterFolder(entry) {
        folderPath = folderPath.concat([{ id: entry.folderId, title: entry.title }])
        list.focusRow(0)
    }

    function goBack() {
        if (!isInFolder)
            return false
        folderPath = folderPath.slice(0, -1)
        list.focusRow(0)
        return true
    }

    function openEntry(entry, background) {
        if (entry.isFolder)
            enterFolder(entry)
        else
            openBookmark(entry, background)
    }

    function openBookmark(entry, background) {
        browserWindow.openUrl(entry.url, background)
        if (!background)
            close()
    }

    function openAllInTabs() {
        folderBookmarks.slice().reverse().forEach(function(entry) { browserWindow.openUrl(entry.url, true) })
        close()
    }

    function manageBookmarks() {
        close()
        browserWindow.openBookmarks()
    }

    function closeAndFocusPage() {
        close()
        if (tab)
            tab.focusPage()
    }

    function isBackKey(key) {
        return key === Qt.Key_Backspace || key === (isRightToLeft ? Qt.Key_Right : Qt.Key_Left)
    }

    function focusInitial() {
        if (search.visible)
            search.forceActiveFocus()
        else if (list.visible)
            list.focusRow(0)
        else
            contentItem.forceActiveFocus()
    }

    x: parent ? parent.width - width : 0
    y: parent ? parent.height : 0
    width: Kirigami.Units.gridUnit * 18
    padding: 0
    modal: false
    focus: true
    closePolicy: Popup.CloseOnPressOutsideParent
    onTabChanged: close()
    onAboutToShow: resetLevel()
    onOpened: focusInitial()

    BookmarksPanelEntries {
        id: content
        folderPath: root.folderPath
        query: search.text
    }

    contentItem: ColumnLayout {
        spacing: 0
        Keys.onEscapePressed: root.closeAndFocusPage()
        Keys.onPressed: function(event) { event.accepted = root.isBackKey(event.key) && root.goBack() }

        BookmarksPanelHeader {
            visible: root.isInFolder
            title: root.isInFolder ? root.folderPath[root.folderPath.length - 1].title : ""
            onBackRequested: root.goBack()
        }

        PanelSearchField {
            id: search
            placeholderText: qsTr("Search bookmarks")
            visible: !root.isInFolder && content.hasBookmarks
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            onStepDownRequested: list.focusRow(0)
            onOpenRequested: function(background) { list.openCurrent(background) }
        }

        Kirigami.Separator {
            visible: root.isInFolder
            Layout.fillWidth: true
        }

        BookmarksPanelList {
            id: list
            visible: root.isInFolder || content.hasBookmarks
            entries: content.entries
            emptyText: content.isSearching ? qsTr("No bookmarks match") : qsTr("Empty folder")
            Layout.fillWidth: true
            onEntryOpened: function(entry, background) { root.openEntry(entry, background) }
            onBackRequested: root.goBack()
            onTopReached: search.visible ? search.forceActiveFocus() : list.focusRow(0)
        }

        Kirigami.PlaceholderMessage {
            visible: !root.isInFolder && !content.hasBookmarks
            icon.name: "bookmarks"
            text: qsTr("No Bookmarks")
            explanation: qsTr("Bookmarked pages show up here.")
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.largeSpacing * 2
        }

        Kirigami.Separator { Layout.fillWidth: true }

        BookmarksPanelFooter {
            isFolder: root.isInFolder
            canOpenAll: root.folderBookmarks.length > 0
            Layout.fillWidth: true
            onOpenAllRequested: root.openAllInTabs()
            onManageRequested: root.manageBookmarks()
        }
    }
}
