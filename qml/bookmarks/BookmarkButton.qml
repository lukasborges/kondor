import QtQuick
import QtQuick.Controls
import Kondor

ToolButton {
    id: root

    required property TabModel tabs

    readonly property alias editor: editorPopup

    visible: tabs.currentTab && tabs.currentTab.url.toString().length > 0
    enabled: tabs.currentTab ? !tabs.currentTab.newTabPage : false
    display: AbstractButton.IconOnly
    icon.name: editor.pageBookmarked ? "bookmarks-bookmarked" : "bookmarks"
    icon.width: 16
    icon.height: 16
    flat: true
    implicitWidth: 28
    implicitHeight: 28
    ToolTip.visible: hovered
    Accessible.name: ToolTip.text
    ToolTip.text: editor.pageBookmarked ? qsTr("Edit This Bookmark") : qsTr("Bookmark This Page")
    ToolTip.delay: 600
    onClicked: editorPopup.opened ? editorPopup.close() : editorPopup.openEditor()

    BookmarkEditorPopup {
        id: editorPopup
        tabs: root.tabs
    }
}
