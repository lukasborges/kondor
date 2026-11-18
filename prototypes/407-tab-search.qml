// #407 Tab search: Ctrl+Shift+A or the button at the end of the tab row lists the tabs of every
// normal window; typing filters them by title and address, Enter switches to the selected one.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

TabStyleFrame {
    id: frame
    height: 600
    tabStyle: "floating"
    withTabSearch: true
    tabs: [
        { title: "Mail", icon: "internet-mail", pinned: true },
        { title: "KDE Community", icon: "kde" },
        { title: "Kirigami documentation", icon: "text-html" },
        { title: "Plasma 6 launch video", icon: "plasma" },
        { title: "Qt WebEngine overview", icon: "qtcreator" }
    ]
    currentTab: 1

    component SectionHeader: Kirigami.ListSectionHeader {
        Layout.fillWidth: true
    }

    component TabRow: ItemDelegate {
        id: row
        property string title
        property string address
        property string iconName
        property bool isCurrent: false
        Layout.fillWidth: true
        contentItem: RowLayout {
            spacing: Kirigami.Units.largeSpacing
            Kirigami.Icon {
                source: row.iconName
                Layout.preferredWidth: Kirigami.Units.iconSizes.small
                Layout.preferredHeight: Kirigami.Units.iconSizes.small
            }
            ColumnLayout {
                spacing: 0
                Layout.fillWidth: true
                Label { text: row.title; textFormat: Text.StyledText; elide: Text.ElideRight; Layout.fillWidth: true }
                Label {
                    text: row.address
                    textFormat: Text.StyledText
                    elide: Text.ElideMiddle
                    color: row.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.disabledTextColor
                    opacity: row.highlighted ? 0.8 : 1
                    font: Kirigami.Theme.smallFont
                    Layout.fillWidth: true
                }
            }
            Kirigami.Icon {
                visible: row.isCurrent
                source: "checkmark"
                Layout.preferredWidth: Kirigami.Units.iconSizes.small
                Layout.preferredHeight: Kirigami.Units.iconSizes.small
            }
            ToolButton {
                visible: row.highlighted
                display: AbstractButton.IconOnly
                icon.name: "window-close-symbolic"
                ToolTip.text: "Close Tab"
                ToolTip.delay: 600
                Accessible.name: "Close Tab"
            }
        }
    }

    Popup {
        popupType: Popup.Item
        x: frame.width - width - Kirigami.Units.smallSpacing
        y: Kirigami.Units.gridUnit * 2 + Kirigami.Units.smallSpacing * 2
        width: Kirigami.Units.gridUnit * 24
        padding: Kirigami.Units.smallSpacing
        Component.onCompleted: open()
        contentItem: ColumnLayout {
            spacing: Kirigami.Units.smallSpacing
            Kirigami.SearchField {
                Layout.fillWidth: true
                placeholderText: "Search tabs"
                text: "kde"
            }
            SectionHeader { text: "This Window" }
            TabRow {
                title: "<b>KDE</b> Community"
                address: "<b>kde</b>.org"
                iconName: "kde"
                isCurrent: true
            }
            TabRow {
                title: "Kirigami documentation"
                address: "develop.<b>kde</b>.org/docs/getting-started/kirigami"
                iconName: "text-html"
                highlighted: true
            }
            TabRow {
                title: "Plasma 6 launch video"
                address: "<b>kde</b>.org/announcements/megarelease/6"
                iconName: "plasma"
            }
            SectionHeader { text: "Window 2" }
            TabRow {
                title: "<b>KDE</b> Bugtracking System"
                address: "bugs.<b>kde</b>.org"
                iconName: "kde"
            }
            TabRow {
                title: "Planet <b>KDE</b>"
                address: "planet.<b>kde</b>.org"
                iconName: "internet-web-browser"
            }
        }
    }
}
