pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ToolBar {
    id: root

    required property TabModel tabModel

    function openBookmark(url, background) {
        const tab = root.tabModel.currentTab
        if (!tab || !url)
            return
        if (background)
            root.openInBackgroundTab(tab, url)
        else
            tab.navigateTo(url)
    }

    function openInBackgroundTab(tab, url) {
        const profile = tab.isPrivate ? ProfileManager.createPrivateProfile()
                                      : ProfileManager.defaultProfile()
        root.tabModel.addTabWithProfile(profile, url, true)
    }

    function activate(button) {
        if (!button.isFolder)
            return root.openBookmark(button.url, BookmarkManager.ctrlPressed())
        folderMenu.folderId = button.id
        folderMenu.popup(button, 0, button.height)
    }

    visible: Settings.showBookmarksBar
    Kirigami.Theme.colorSet: Kirigami.Theme.Window
    Kirigami.Theme.inherit: false
    position: ToolBar.Header

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 4
        anchors.rightMargin: 4
        spacing: 2

        Repeater {
            model: BookmarkManager.toolbarModel

            delegate: ToolButton {
                id: barButton

                required property int id
                required property string title
                required property string url
                required property bool isFolder

                flat: true
                padding: Kirigami.Units.smallSpacing
                Accessible.name: barButton.title
                ToolTip.visible: hovered
                ToolTip.text: barButton.isFolder ? barButton.title : barButton.url
                ToolTip.delay: 600

                contentItem: RowLayout {
                    spacing: Kirigami.Units.smallSpacing

                    Kirigami.Icon {
                        visible: barButton.isFolder
                        source: "folder"
                        Layout.preferredWidth: 16
                        Layout.preferredHeight: 16
                    }

                    SiteIcon {
                        visible: !barButton.isFolder
                        pageUrl: barButton.url
                        Layout.preferredWidth: 16
                        Layout.preferredHeight: 16
                    }

                    Label {
                        Layout.maximumWidth: Kirigami.Units.gridUnit * 14
                        text: barButton.title.length ? barButton.title : barButton.url
                        elide: Text.ElideRight
                    }
                }

                onClicked: root.activate(barButton)

                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.MiddleButton
                    onClicked: if (!barButton.isFolder) root.openBookmark(barButton.url, true)
                }
            }
        }

        Item { Layout.fillWidth: true }
    }

    BookmarkMenu {
        id: folderMenu
        onBookmarkActivated: function(url, background) {
            root.openBookmark(url, background)
        }
    }
}
