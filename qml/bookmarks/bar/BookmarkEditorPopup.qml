import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Popup {
    id: root

    required property TabModel tabs

    property var editingId: -1
    property bool justAdded: false

    readonly property bool pageBookmarked: {
        const revision = BookmarkManager.revision
        const tab = tabs.currentTab
        return revision >= 0 && tab !== null && tab.url.toString().length > 0
            && BookmarkManager.isBookmarked(tab.url)
    }

    function isBookmarkable(tab) {
        return tab !== null && !tab.newTabPage && tab.url.toString().length > 0
    }

    function openEditor() {
        const tab = tabs.currentTab
        if (!isBookmarkable(tab))
            return
        const existingId = BookmarkManager.bookmarkIdFor(tab.url)
        if (existingId > 0)
            edit(existingId, false)
        else
            addAndEdit(tab)
    }

    function addAndEdit(tab) {
        const id = BookmarkManager.addBookmark(tab.url, tab.title, BookmarkManager.otherFolderId())
        if (id > 0)
            edit(id, true)
    }

    function edit(id, added) {
        const info = BookmarkManager.bookmark(id)
        editingId = id
        justAdded = added
        titleField.text = info.title
        folderBox.model = BookmarkManager.folders
        folderBox.currentIndex = Math.max(0, folderBox.model.findIndex(folder => folder.id === info.parentId))
        open()
    }

    function save() {
        if (editingId <= 0)
            return
        renameFromField()
        moveToSelectedFolder()
        close()
    }

    function renameFromField() {
        const title = titleField.text.trim()
        if (title.length > 0)
            BookmarkManager.rename(editingId, title)
    }

    function moveToSelectedFolder() {
        const folders = folderBox.model
        const index = folderBox.currentIndex
        if (index < 0 || index >= folders.length)
            return
        if (BookmarkManager.bookmark(editingId).parentId !== folders[index].id)
            BookmarkManager.move(editingId, folders[index].id, -1)
    }

    function remove() {
        if (editingId > 0)
            BookmarkManager.remove(editingId)
        close()
    }

    x: parent.width - width
    y: parent.height
    width: Kirigami.Units.gridUnit * 20
    padding: Kirigami.Units.largeSpacing

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.Heading {
            level: 4
            text: root.justAdded ? qsTr("Page bookmarked") : qsTr("Edit Bookmark")
        }

        Kirigami.FormLayout {
            Layout.fillWidth: true

            TextField {
                id: titleField
                Kirigami.FormData.label: qsTr("Name:")
                Layout.fillWidth: true
            }

            ComboBox {
                id: folderBox
                Kirigami.FormData.label: qsTr("Folder:")
                Layout.fillWidth: true
                textRole: "title"
            }
        }

        RowLayout {
            Layout.fillWidth: true

            Button {
                text: qsTr("Remove")
                icon.name: "edit-delete"
                onClicked: root.remove()
            }

            Item { Layout.fillWidth: true }

            Button {
                text: qsTr("Done")
                icon.name: "dialog-ok-apply"
                highlighted: true
                onClicked: root.save()
            }
        }
    }
}
