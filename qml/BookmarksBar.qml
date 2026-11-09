pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// Thin bar under the navigation toolbar with the "Bookmarks Toolbar" folder.
// Shown with Ctrl+Shift+B (Settings.showBookmarksBar).
ToolBar {
    id: root

    required property TabModel tabModel

    function openBookmark(url, background) {
        const tab = root.tabModel.currentTab
        if (!tab || !url)
            return
        if (background) {
            // A new tab keeps the current mode: private stays private.
            const profile = tab.isPrivate ? ProfileManager.createPrivateProfile()
                                          : ProfileManager.defaultProfile()
            root.tabModel.addTabWithProfile(profile, url, true)
        } else {
            tab.navigateTo(url)
        }
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

                    Label {
                        Layout.maximumWidth: Kirigami.Units.gridUnit * 14
                        text: barButton.title.length ? barButton.title : barButton.url
                        elide: Text.ElideRight
                    }
                }

                onClicked: {
                    if (barButton.isFolder) {
                        folderMenu.folderId = barButton.id
                        folderMenu.popup(barButton)
                    } else {
                        root.openBookmark(barButton.url, BookmarkManager.ctrlPressed())
                    }
                }

                // Middle click opens the bookmark in a background tab; the
                // button itself only handles the left button.
                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.MiddleButton
                    onClicked: {
                        if (!barButton.isFolder)
                            root.openBookmark(barButton.url, true)
                    }
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
