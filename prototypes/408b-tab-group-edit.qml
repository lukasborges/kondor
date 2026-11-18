// #408 Tab groups: right-clicking a group's label (or Menu on it) opens its editor: name, color and
// the group actions. A left click on the label collapses or expands the group.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

TabStyleFrame {
    id: frame
    height: 460
    tabStyle: "floating"
    tabWidth: 200
    tabs: [
        { title: "Mail", icon: "internet-mail", pinned: true },
        { chip: true, title: "Work", group: "blue" },
        { title: "KDE Community", icon: "kde", group: "blue" },
        { title: "Kirigami documentation", icon: "text-html", group: "blue" },
        { chip: true, title: "Reading", group: "green", collapsed: true, count: 3 },
        { title: "Qt WebEngine overview", icon: "qtcreator" }
    ]
    currentTab: 2

    component ColorSwatch: AbstractButton {
        id: swatch
        property string colorName
        implicitWidth: Kirigami.Units.gridUnit * 1.5
        implicitHeight: implicitWidth
        ToolTip.text: text
        ToolTip.delay: 600
        Accessible.name: text
        contentItem: Rectangle {
            radius: width / 2
            color: frame.groupColor(swatch.colorName)
            border.width: swatch.checked ? 2 : 0
            border.color: Kirigami.Theme.textColor
            Kirigami.Icon {
                visible: swatch.checked
                anchors.centerIn: parent
                width: 14; height: 14
                source: "checkmark"
                color: "white"
                isMask: true
            }
        }
    }

    Popup {
        popupType: Popup.Item
        x: 44
        y: Kirigami.Units.gridUnit * 2 + Kirigami.Units.smallSpacing * 2
        width: Kirigami.Units.gridUnit * 16
        padding: Kirigami.Units.largeSpacing
        Component.onCompleted: open()
        contentItem: ColumnLayout {
            spacing: Kirigami.Units.largeSpacing
            TextField {
                Layout.fillWidth: true
                text: "Work"
                placeholderText: "Group name"
                Accessible.name: "Group name"
            }
            RowLayout {
                spacing: Kirigami.Units.smallSpacing
                ColorSwatch { colorName: "blue"; text: "Blue"; checked: true }
                ColorSwatch { colorName: "green"; text: "Green" }
                ColorSwatch { colorName: "orange"; text: "Orange" }
                ColorSwatch { colorName: "red"; text: "Red" }
                ColorSwatch { colorName: "purple"; text: "Purple" }
                ColorSwatch { colorName: "gray"; text: "Gray" }
            }
            Kirigami.Separator { Layout.fillWidth: true }
            ColumnLayout {
                spacing: 0
                Layout.fillWidth: true
                ItemDelegate { Layout.fillWidth: true; text: "New Tab in Group"; icon.name: "tab-new" }
                ItemDelegate { Layout.fillWidth: true; text: "Collapse Group"; icon.name: "arrow-up" }
                ItemDelegate { Layout.fillWidth: true; text: "Move Group to New Window"; icon.name: "window-new" }
                ItemDelegate { Layout.fillWidth: true; text: "Ungroup Tabs"; icon.name: "object-ungroup" }
                ItemDelegate { Layout.fillWidth: true; text: "Close Group"; icon.name: "tab-close" }
            }
        }
    }
}
