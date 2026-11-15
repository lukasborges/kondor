import QtQml
import Kondor

QtObject {
    id: root

    property var folderPath: []
    property string query: ""

    readonly property int recentLimit: 5
    readonly property int searchLimit: 50
    readonly property bool isSearching: query.trim() !== ""
    readonly property int folderId: folderPath.length > 0 ? folderPath[folderPath.length - 1].id : 0
    readonly property var entries: collect(BookmarkManager.revision)
    readonly property bool hasBookmarks: countRootItems(BookmarkManager.revision) > 0

    function collect(revision) {
        if (isSearching)
            return entriesOf(BookmarkManager.search(query, searchLimit), "")
        if (folderId > 0)
            return entriesOf(BookmarkManager.folderContents(folderId), "")
        return entriesOf(BookmarkManager.recentBookmarks(recentLimit), qsTr("Recently Added"))
                .concat(rootFolders())
    }

    function countRootItems(revision) {
        return BookmarkManager.childCount(BookmarkManager.toolbarFolderId())
                + BookmarkManager.childCount(BookmarkManager.otherFolderId())
    }

    function entriesOf(rows, section) {
        return rows.map(function(row) { return entryOf(row, section) })
    }

    function entryOf(row, section) {
        const isFolder = row.isFolder === true
        return {
            title: row.title.length > 0 ? row.title : row.url,
            url: row.url ?? "",
            isFolder: isFolder,
            folderId: isFolder ? row.id : 0,
            count: isFolder ? BookmarkManager.childCount(row.id) : 0,
            iconName: "folder",
            section: section
        }
    }

    function rootFolders() {
        return [
            rootFolder(BookmarkManager.toolbarFolderId(), qsTr("Bookmarks Toolbar"), "bookmark-toolbar"),
            rootFolder(BookmarkManager.otherFolderId(), qsTr("Other Bookmarks"), "folder")
        ]
    }

    function rootFolder(id, title, iconName) {
        const entry = entryOf({ id: id, title: title, url: "", isFolder: true }, qsTr("Folders"))
        entry.iconName = iconName
        return entry
    }
}
