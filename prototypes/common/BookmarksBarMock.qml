// #229 Bookmarks bar: folders with an arrow, an overflow menu for the items that do not fit, a
// drop indicator while dragging, and folder actions. Static mock.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ToolBar {
    id: bar

    // Index of the gap that shows the drop indicator, or -1.
    property int dropAt: -1
    property int pressedIndex: -1
    // Items shown on the bar; the rest is in the » menu, which only shows when something is left out.
    property int visibleCount: items.length

    readonly property var items: [
        { t: "KDE", i: "kde" }, { t: "Planet KDE", i: "globe" }, { t: "Qt Docs", i: "globe" },
        { t: "News", i: "folder", f: true }, { t: "Development", i: "folder", f: true },
        { t: "Linux Weekly News", i: "globe" }, { t: "Wikipedia", i: "internet-web-browser" },
        { t: "Kirigami Gallery", i: "kde" }
    ]

    Layout.fillWidth: true
    position: ToolBar.Header

    component Item_: ToolButton {
        property var data_
        property int index_
        flat: true
        checked: index_ === bar.pressedIndex
        contentItem: RowLayout {
            spacing: Kirigami.Units.smallSpacing
            Kirigami.Icon { source: data_.i; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
            Label { text: data_.t; elide: Text.ElideRight; Layout.maximumWidth: Kirigami.Units.gridUnit * 9 }
            Kirigami.Icon { visible: !!data_.f; source: "arrow-down"; Layout.preferredWidth: 10; Layout.preferredHeight: 10 }
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 2
        Repeater {
            model: bar.items
            RowLayout {
                visible: index < bar.visibleCount
                required property var modelData
                required property int index
                spacing: 0
                Rectangle { visible: bar.dropAt === index; width: 2; height: 22; radius: 1; color: Kirigami.Theme.highlightColor }
                Item_ { data_: modelData; index_: index }
            }
        }
        Item { Layout.fillWidth: true }
        ToolButton {
            visible: bar.visibleCount < bar.items.length
            icon.name: "arrow-right-double"
            display: AbstractButton.IconOnly
            flat: true
            checked: bar.pressedIndex === 99
            ToolTip.text: "More Bookmarks"
        }
    }
}
