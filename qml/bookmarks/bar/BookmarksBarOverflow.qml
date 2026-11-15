import QtQuick
import QtQuick.Controls
import Kondor

ToolButton {
    id: root

    required property int skippedCount

    readonly property bool isRightToLeft: Qt.application.layoutDirection === Qt.RightToLeft

    signal bookmarkActivated(string url, bool background)

    icon.name: root.isRightToLeft ? "arrow-left-double" : "arrow-right-double"
    display: AbstractButton.IconOnly
    flat: true
    Accessible.name: ToolTip.text
    ToolTip.visible: hovered
    ToolTip.text: qsTr("More Bookmarks")
    ToolTip.delay: 600
    onClicked: menu.popup(root, 0, root.height)

    BookmarkMenu {
        id: menu
        folderId: BookmarkManager.toolbarFolderId()
        skippedCount: root.skippedCount
        onBookmarkActivated: function(url, background) { root.bookmarkActivated(url, background) }
    }
}
