// #227 Bookmarks panel, opened by the toolbar button (or Ctrl+B). Static mock, same structure as
// the Extensions panel (#183): a list level, a folder level, search results, and an empty state.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Popup {
    id: panel

    // "list" | "folder" | "search" | "empty"
    property string level: "list"
    property string query: ""

    popupType: Popup.Item
    width: Kirigami.Units.gridUnit * 18
    padding: 0
    Component.onCompleted: open()

    component Row: ItemDelegate {
        property string iconName: "globe"
        property bool folder: false
        property string detail: ""
        Layout.fillWidth: true
        contentItem: RowLayout {
            spacing: Kirigami.Units.smallSpacing
            Kirigami.Icon { source: iconName; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
            Label { text: parent.parent.text; Layout.fillWidth: true; elide: Text.ElideRight }
            Label { visible: detail !== ""; text: detail; opacity: 0.6 }
            Kirigami.Icon { visible: folder; source: "go-next-symbolic"; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
        }
    }

    contentItem: ColumnLayout {
        spacing: 0

        RowLayout {
            visible: panel.level === "folder"
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            ToolButton { icon.name: "go-previous-symbolic"; display: AbstractButton.IconOnly }
            Kirigami.Heading { level: 4; text: "News"; Layout.fillWidth: true }
        }

        TextField {
            visible: panel.level !== "folder" && panel.level !== "empty"
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            placeholderText: "Search bookmarks"
            text: panel.query
            focus: true
            leftPadding: 26
            Kirigami.Icon { source: "edit-find"; width: 16; height: 16; x: 6; anchors.verticalCenter: parent.verticalCenter }
        }
        Kirigami.Separator { Layout.fillWidth: true; visible: panel.level === "folder" }

        ColumnLayout {
            visible: panel.level === "list"
            spacing: 0
            Kirigami.ListSectionHeader { Layout.fillWidth: true; text: "Recently Added" }
            Row { text: "OMG! Ubuntu"; iconName: "globe" }
            Row { text: "Kondor Browser"; iconName: "github" }
            Row { text: "KDE Human Interface Guidelines"; iconName: "kde" }
            Kirigami.ListSectionHeader { Layout.fillWidth: true; text: "Folders" }
            Row { text: "Bookmarks Toolbar"; iconName: "bookmark-toolbar"; folder: true; detail: "6" }
            Row { text: "Other Bookmarks"; iconName: "folder"; folder: true; detail: "24" }
        }

        ColumnLayout {
            visible: panel.level === "folder"
            spacing: 0
            Row { text: "Weekly"; iconName: "folder"; folder: true; detail: "3" }
            Row { text: "OMG! Ubuntu"; iconName: "globe" }
            Row { text: "Phoronix"; iconName: "globe"; highlighted: true }
            Row { text: "LWN.net"; iconName: "globe" }
            Row { text: "This Week in KDE"; iconName: "kde" }
        }

        ColumnLayout {
            visible: panel.level === "search"
            spacing: 0
            Row { text: "KDE Community"; iconName: "kde"; highlighted: true }
            Row { text: "KDE Human Interface Guidelines"; iconName: "kde" }
            Row { text: "This Week in KDE"; iconName: "kde" }
            Row { text: "KDE Eco"; iconName: "kde" }
        }

        Kirigami.PlaceholderMessage {
            visible: panel.level === "empty"
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.largeSpacing * 2
            icon.name: "bookmarks"
            text: "No Bookmarks"
            explanation: "Bookmarked pages show up here."
        }

        Kirigami.Separator { Layout.fillWidth: true }
        RowLayout {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            Button {
                visible: panel.level === "folder"
                text: "Open All in Tabs"
                icon.name: "tab-new"
                flat: true
            }
            Switch { visible: panel.level !== "folder"; text: "Show Bookmarks Bar"; checked: true }
            Item { Layout.fillWidth: true }
            ToolButton { icon.name: "configure"; display: AbstractButton.IconOnly; Accessible.name: "Manage Bookmarks"; ToolTip.text: "Manage Bookmarks"; ToolTip.delay: 600
            }
        }
    }
}
