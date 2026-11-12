import QtQuick
import QtQuick.Controls

Menu {
    id: root

    property string entryUrl: ""
    property int entryId: -1

    signal openRequested(string url)

    function popupFor(entry, x, y) {
        root.entryUrl = entry.url
        root.entryId = entry.id
        root.popup(entry, x, y)
    }

    function copyAddress(text) {
        clipboardHelper.text = text
        clipboardHelper.selectAll()
        clipboardHelper.copy()
    }

    TextEdit {
        id: clipboardHelper
        visible: false
    }

    MenuItem {
        text: qsTr("Open in New Tab")
        icon.name: "tab-new"
        onTriggered: root.openRequested(root.entryUrl)
    }
    MenuItem {
        text: qsTr("Copy Address")
        icon.name: "edit-copy"
        onTriggered: root.copyAddress(root.entryUrl)
    }
    MenuSeparator {}
    MenuItem {
        text: qsTr("Remove from History")
        icon.name: "edit-delete"
        onTriggered: HistoryManager.removeEntry(root.entryId)
    }
}
