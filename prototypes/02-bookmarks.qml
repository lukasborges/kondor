// #2 Bookmarks — star in the address bar, edit popup (Ctrl+D) and bookmarks toolbar.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    addressRight: [
        ToolButton {
            icon.name: "bookmarks-bookmarked" // bookmarked, filled (not bookmarked: "bookmarks", outline)
            icon.width: 16; icon.height: 16
            display: AbstractButton.IconOnly
            flat: true
            implicitWidth: 28; implicitHeight: 28
        }
    ]
    belowHeader: [
        // Bookmarks toolbar (Ctrl+Shift+B)
        ToolBar {
            Layout.fillWidth: true
            Kirigami.Theme.colorSet: Kirigami.Theme.Window
            Kirigami.Theme.inherit: false
            position: ToolBar.Header
            RowLayout {
                spacing: 2
                Repeater {
                    model: [
                        { t: "KDE", i: "kde" }, { t: "Planet KDE", i: "globe" },
                        { t: "Qt Docs", i: "globe" }, { t: "News", i: "folder" },
                        { t: "Development", i: "folder" }, { t: "Linux", i: "folder" }
                    ]
                    ToolButton {
                        text: modelData.t
                        icon.name: modelData.i
                        icon.width: 16; icon.height: 16
                        display: AbstractButton.TextBesideIcon
                        flat: true
                    }
                }
            }
        }
    ]
    FakePage {}

    Popup {
        popupType: Popup.Item
        x: frame.width - width - 50
        y: -4
        width: 330
        padding: Kirigami.Units.largeSpacing
        Component.onCompleted: open()
        contentItem: ColumnLayout {
            spacing: Kirigami.Units.largeSpacing
            Kirigami.Heading { level: 4; text: "Page bookmarked" }
            Kirigami.FormLayout {
                Layout.fillWidth: true
                TextField { Kirigami.FormData.label: "Name:"; text: "KDE Community"; Layout.fillWidth: true }
                ComboBox { Kirigami.FormData.label: "Folder:"; model: ["Bookmarks Toolbar", "Other Bookmarks", "News"]; Layout.fillWidth: true }
            }
            RowLayout {
                Layout.fillWidth: true
                Button { text: "Remove"; icon.name: "edit-delete" }
                Item { Layout.fillWidth: true }
                Button { text: "Done"; icon.name: "dialog-ok-apply"; highlighted: true }
            }
        }
    }
}
