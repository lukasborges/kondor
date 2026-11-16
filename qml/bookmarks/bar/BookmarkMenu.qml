import QtQuick
import QtQuick.Controls
import Kondor

Menu {
    id: root

    MenuKeyNavigation { menu: root }

    property var folderId: -1
    property bool showCommands: false
    property bool showFolderActions: false
    property bool canAddPage: false
    property int skippedCount: 0

    signal bookmarkActivated(string url, bool background)
    signal bookmarkThisPageRequested()
    signal manageBookmarksRequested()
    signal openAllRequested()
    signal addPageRequested()

    readonly property int staticCount: 4

    onAboutToShow: root.rebuild()

    function rebuild() {
        root.removeDynamicItems()
        if (root.folderId > 0)
            root.appendFolder(root, root.folderId, 0)
        if (root.showFolderActions)
            root.appendFolderActions()
    }

    function appendFolderActions() {
        const count = BookmarkManager.folderContents(root.folderId).filter(entry => !entry.isFolder).length
        if (count === 0 && !root.canAddPage)
            return
        root.addItem(separatorComponent.createObject(null))
        if (count > 0)
            root.addItem(openAllComponent.createObject(null, { count: count }))
        if (root.canAddPage)
            root.addItem(addPageComponent.createObject(null))
    }

    function entriesOf(id, depth) {
        const skipped = depth === 0 ? root.skippedCount : 0
        return BookmarkManager.folderContents(id).slice(skipped).filter(entry => !entry.isFolder || depth < 8)
    }

    function removeDynamicItems() {
        while (root.count > root.staticCount && root.itemAt(root.count - 1))
            root.removeItem(root.itemAt(root.count - 1))
    }

    function appendFolder(menu, id, depth) {
        const entries = root.entriesOf(id, depth)
        entries.forEach(function(entry) { root.appendEntry(menu, entry, depth) })
        if (entries.length === 0)
            menu.addItem(emptyComponent.createObject(null))
    }

    function appendEntry(menu, entry, depth) {
        if (entry.isFolder)
            root.appendSubmenu(menu, entry, depth)
        else
            root.appendBookmark(menu, entry)
    }

    function appendSubmenu(menu, entry, depth) {
        const submenu = menuComponent.createObject(null, { title: entry.title })
        root.appendFolder(submenu, entry.id, depth + 1)
        menu.addMenu(submenu)
    }

    function appendBookmark(menu, entry) {
        const item = bookmarkComponent.createObject(null, {
            pageUrl: entry.url,
            label: entry.title.length ? entry.title : entry.url
        })
        item["triggered"].connect(function() {
            root.bookmarkActivated(entry.url, BookmarkManager.ctrlPressed())
        })
        menu.addItem(item)
    }

    MenuItem {
        visible: root.showCommands
        text: qsTr("Bookmark This Page")
        icon.name: "bookmark-new"
        onTriggered: root.bookmarkThisPageRequested()
    }
    MenuItem {
        visible: root.showCommands
        text: qsTr("Manage Bookmarks…")
        icon.name: "bookmarks-organize"
        onTriggered: root.manageBookmarksRequested()
    }
    MenuItem {
        id: toolbarToggle
        visible: root.showCommands
        text: qsTr("Show Bookmarks Toolbar")
        checkable: true
        checked: Settings.showBookmarksBar
        onToggled: Settings.showBookmarksBar = checked
    }
    MenuSeparator {
        visible: root.showCommands
    }

    Component {
        id: bookmarkComponent
        SiteMenuItem {}
    }

    Component {
        id: menuComponent
        Menu {
            icon.name: "folder"
        }
    }

    Component {
        id: separatorComponent
        MenuSeparator {}
    }

    Component {
        id: openAllComponent
        MenuItem {
            required property int count

            text: qsTr("Open All in Tabs (%1)").arg(count)
            icon.name: "tab-new"
            onTriggered: root.openAllRequested()
        }
    }

    Component {
        id: addPageComponent
        MenuItem {
            text: qsTr("Add This Page Here")
            icon.name: "bookmark-new"
            onTriggered: root.addPageRequested()
        }
    }

    Component {
        id: emptyComponent
        MenuItem {
            text: qsTr("(Empty)")
            enabled: false
        }
    }

    Connections {
        target: Settings

        function onShowBookmarksBarChanged() {
            toolbarToggle.checked = Settings.showBookmarksBar
        }
    }
}
