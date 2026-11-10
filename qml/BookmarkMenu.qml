import QtQuick
import QtQuick.Controls
import Kondor

// A menu that lists the contents of one bookmark folder. Used for the folders
// in the bookmarks bar and, with `showCommands`, as the main menu's
// "Bookmarks" submenu. The items are built when the menu opens, so they always
// reflect the database.
Menu {
    id: root

    // Folder to list. -1 lists nothing (the commands of the main menu only).
    property var folderId: -1
    // Show the bookmark commands above the folder contents.
    property bool showCommands: false

    signal bookmarkActivated(string url, bool background)
    signal bookmarkThisPageRequested()
    signal manageBookmarksRequested()

    // The four static children below; everything after them is rebuilt.
    readonly property int staticCount: 4

    onAboutToShow: root.rebuild()

    function rebuild() {
        while (root.count > root.staticCount) {
            const item = root.itemAt(root.count - 1)
            if (!item)
                break
            // removeItem deletes the item, unlike takeItem.
            root.removeItem(item)
        }
        if (root.folderId > 0)
            root.appendFolder(root, root.folderId, 0)
    }

    function appendFolder(menu, id, depth) {
        const entries = BookmarkManager.folderContents(id)
        let added = 0
        for (let i = 0; i < entries.length; ++i) {
            const entry = entries[i]
            if (entry.isFolder) {
                // Deeply nested folders are not much use in a menu; the
                // manager window shows the whole tree anyway.
                if (depth >= 8)
                    continue
                const submenu = menuComponent.createObject(null)
                submenu.title = entry.title
                // qmllint disable missing-property
                submenu.icon.name = "folder"
                // qmllint enable missing-property
                root.appendFolder(submenu, entry.id, depth + 1)
                menu.addMenu(submenu)
                ++added
            } else {
                const item = bookmarkComponent.createObject(null)
                item.text = entry.title.length ? entry.title : entry.url
                const url = entry.url
                // qmllint disable missing-property
                item.triggered.connect(function() {
                    root.bookmarkActivated(url, BookmarkManager.ctrlPressed())
                })
                // qmllint enable missing-property
                menu.addItem(item)
                ++added
            }
        }
        // An empty folder still opens a normal-sized menu with a disabled
        // "(Empty)" item, like Firefox, instead of a blank popup.
        if (added === 0)
            menu.addItem(emptyComponent.createObject(null))
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
        MenuItem {}
    }

    Component {
        id: menuComponent
        Menu {}
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
